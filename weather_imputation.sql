use ElectricLoadForecast
go

-------------- Tables used ----------------
-- man.mi_weather_weather_obs_daily is main daily weather from CIAP
			--the record_type field means whether data is from original
			--weather data or refilled by using nearest stations
-- man.mi_weather_weather_obs_daily_refilled is the filled weather data
			--that includes all dates for each weather station
-- man.Calendar is a full list of all dates from 1900 to 2100
-- man.WEATHER_STATION gives the list of stations and their nearest stations

-------------- Set initial parameters ----------------
declare @year_back int = 13; --This is to define # of years of history in data
declare @earliest_weather_date date = cast(cast((year(getdate())-@year_back) as varchar(max))+'-01-01' as DATE);
---- Extract all dates for each station
if object_id('tempdb..#refilled_weather_1') is not null
	drop table #refilled_weather_1;
with stat as (
select STATION, min(OPR_DATE) opr_date_min, max(OPR_DATE) opr_date_max
	from man.mi_weather_weather_obs_daily
	group by STATION)
,
cal as (
select distinct Date from man.Calendar)
,
fullhist as (
select STATION, Date as OPR_DATE
	from stat join cal
	on cal.Date between stat.opr_date_min and stat.opr_date_max)

select coalesce(m.STATION, fullhist.STATION) STATION, coalesce(m.OPR_DATE,fullhist.OPR_DATE) OPR_DATE, 
		m.TEMP_AIR_AVG, m.TEMP_AIR_MIN, m.TEMP_AIR_MAX, 
		m.TEMP_DEW_PT_AVG, m.TEMP_DEW_PT_MIN, m.TEMP_DEW_PT_MAX, m.TEMP_WET_AVG,
		m.TEMP_WET_MIN, m.TEMP_WET_MAX, m.THI_AVG, m.THI_MIN, m.THI_MAX, m.WTHI,
		m.HDD, m.CDD, m.NUM_READINGS_IN_DAY, coalesce(m.RECORD_TYPE,'Refilled') RECORD_TYPE
	into #refilled_weather_1
	from man.mi_weather_weather_obs_daily m
		right join fullhist
	on m.STATION = fullhist.STATION and m.OPR_DATE = fullhist.OPR_DATE ;

---- Find the nearest station's weather info
if object_id('tempdb..#refilled_weather_2') is not null
	drop table #refilled_weather_2;
select m.STATION , m.OPR_DATE , 
		coalesce(m.TEMP_AIR_AVG, orginal_1.TEMP_AIR_AVG, orginal_2.TEMP_AIR_AVG) TEMP_AIR_AVG , 
		coalesce(m.TEMP_AIR_MIN, orginal_1.TEMP_AIR_MIN, orginal_2.TEMP_AIR_MIN) TEMP_AIR_MIN , 
		coalesce(m.TEMP_AIR_MAX, orginal_1.TEMP_AIR_MAX, orginal_2.TEMP_AIR_MAX) TEMP_AIR_MAX , 
		coalesce(m.TEMP_DEW_PT_AVG, orginal_1.TEMP_DEW_PT_AVG, orginal_2.TEMP_DEW_PT_AVG) TEMP_DEW_PT_AVG , 
		coalesce(m.TEMP_DEW_PT_MIN, orginal_1.TEMP_DEW_PT_MIN, orginal_2.TEMP_DEW_PT_MIN) TEMP_DEW_PT_MIN , 
		coalesce(m.TEMP_DEW_PT_MAX, orginal_1.TEMP_DEW_PT_MAX, orginal_2.TEMP_DEW_PT_MAX) TEMP_DEW_PT_MAX , 
		coalesce(m.TEMP_WET_AVG, orginal_1.TEMP_WET_AVG, orginal_2.TEMP_WET_AVG) TEMP_WET_AVG , 
		coalesce(m.TEMP_WET_MIN, orginal_1.TEMP_WET_MIN, orginal_2.TEMP_WET_MIN) TEMP_WET_MIN , 
		coalesce(m.TEMP_WET_MAX, orginal_1.TEMP_WET_MAX, orginal_2.TEMP_WET_MAX) TEMP_WET_MAX , 
		coalesce(m.THI_AVG, orginal_1.THI_AVG, orginal_2.THI_AVG) THI_AVG , 
		coalesce(m.THI_MIN, orginal_1.THI_MIN, orginal_2.THI_MIN) THI_MIN , 
		coalesce(m.THI_MAX, orginal_1.THI_MAX, orginal_2.THI_MAX) THI_MAX , 
		coalesce(m.WTHI, orginal_1.WTHI, orginal_2.WTHI) WTHI , 
		coalesce(m.HDD, orginal_1.HDD, orginal_2.HDD) HDD , 
		coalesce(m.CDD, orginal_1.CDD, orginal_2.CDD) CDD , 
		coalesce(m.NUM_READINGS_IN_DAY, orginal_1.NUM_READINGS_IN_DAY, orginal_2.NUM_READINGS_IN_DAY) NUM_READINGS_IN_DAY , 
		m.RECORD_TYPE
	into #refilled_weather_2
	from #refilled_weather_1 m
	left join man.WEATHER_STATION station
		on m.station = station.station
	left join (select *
			from #refilled_weather_1
			where RECORD_TYPE like '%Original%') orginal_1
		on station.Nearest_Station = orginal_1.STATION 
			and m.OPR_DATE = orginal_1.OPR_DATE
	left join (select *
			from #refilled_weather_1
			where RECORD_TYPE like '%Original%') orginal_2
		on station.Nearest_2nd_Station = orginal_2.STATION 
			and m.OPR_DATE = orginal_2.OPR_DATE 
	where m.OPR_DATE >= @earliest_weather_date;

---- Find weather info by averaging two nearest days
if object_id('tempdb..#weather_avg') is not null
	drop table #weather_avg;
SELECT m.STATION , m.OPR_DATE,
		AVG(b.TEMP_AIR_AVG) TEMP_AIR_AVG , 
		AVG(b.TEMP_AIR_MIN) TEMP_AIR_MIN , 
		AVG(b.TEMP_AIR_MAX) TEMP_AIR_MAX , 
		AVG(b.TEMP_DEW_PT_AVG) TEMP_DEW_PT_AVG , 
		AVG(b.TEMP_DEW_PT_MIN) TEMP_DEW_PT_MIN , 
		AVG(b.TEMP_DEW_PT_MAX) TEMP_DEW_PT_MAX , 
		AVG(b.TEMP_WET_AVG) TEMP_WET_AVG , 
		AVG(b.TEMP_WET_MIN) TEMP_WET_MIN , 
		AVG(b.TEMP_WET_MAX) TEMP_WET_MAX , 
		AVG(b.THI_AVG) THI_AVG , 
		AVG(b.THI_MIN) THI_MIN , 
		AVG(b.THI_MAX) THI_MAX , 
		AVG(b.WTHI) WTHI , 
		AVG(b.HDD) HDD , 
		AVG(b.CDD) CDD , 
		max(b.NUM_READINGS_IN_DAY) NUM_READINGS_IN_DAY
	into #weather_avg
	FROM #refilled_weather_2 m
		join #refilled_weather_2 b
		on m.station = b.station and abs(DATEDIFF(day,m.opr_date,b.opr_date))=1
		group by m.station, m.opr_date ;

if object_id('tempdb..#refilled_weather_3') is not null
	drop table #refilled_weather_3;
	
select m.STATION , m.OPR_DATE,
		coalesce(m.TEMP_AIR_AVG, b.TEMP_AIR_AVG) TEMP_AIR_AVG , 
		coalesce(m.TEMP_AIR_MIN, b.TEMP_AIR_MIN) TEMP_AIR_MIN , 
		coalesce(m.TEMP_AIR_MAX, b.TEMP_AIR_MAX) TEMP_AIR_MAX , 
		coalesce(m.TEMP_DEW_PT_AVG, b.TEMP_DEW_PT_AVG) TEMP_DEW_PT_AVG , 
		coalesce(m.TEMP_DEW_PT_MIN, b.TEMP_DEW_PT_MIN) TEMP_DEW_PT_MIN , 
		coalesce(m.TEMP_DEW_PT_MAX, b.TEMP_DEW_PT_MAX) TEMP_DEW_PT_MAX , 
		coalesce(m.TEMP_WET_AVG, b.TEMP_WET_AVG) TEMP_WET_AVG , 
		coalesce(m.TEMP_WET_MIN, b.TEMP_WET_MIN) TEMP_WET_MIN , 
		coalesce(m.TEMP_WET_MAX, b.TEMP_WET_MAX) TEMP_WET_MAX , 
		coalesce(m.THI_AVG, b.THI_AVG) THI_AVG , 
		coalesce(m.THI_MIN, b.THI_MIN) THI_MIN , 
		coalesce(m.THI_MAX, b.THI_MAX) THI_MAX , 
		coalesce(m.WTHI, b.WTHI) WTHI , 
		coalesce(m.HDD, b.HDD) HDD , 
		coalesce(m.CDD, b.CDD) CDD , 
		coalesce(m.NUM_READINGS_IN_DAY, b.NUM_READINGS_IN_DAY) NUM_READINGS_IN_DAY , 
		m.RECORD_TYPE
	into #refilled_weather_3
	from #refilled_weather_2 m left join #weather_avg b
		on m.station = b.station and m.opr_date = b.opr_date ;

delete from man.mi_weather_weather_obs_daily_refilled;
insert into man.mi_weather_weather_obs_daily_refilled
select STATION, OPR_DATE, TEMP_AIR_AVG, TEMP_AIR_MIN, TEMP_AIR_MAX, TEMP_DEW_PT_AVG, TEMP_DEW_PT_MIN, TEMP_DEW_PT_MAX, TEMP_WET_AVG, TEMP_WET_MIN, TEMP_WET_MAX, THI_AVG, THI_MIN, THI_MAX, WTHI, HDD, CDD, NUM_READINGS_IN_DAY, RECORD_TYPE
	from #refilled_weather_3
	order by station, opr_date ;

---- Drop all temp tables
drop table #refilled_weather_1;
drop table #refilled_weather_2;
drop table #weather_avg;
drop table #refilled_weather_3;