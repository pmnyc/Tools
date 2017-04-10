#ifndef MAP_MATCHING_HPP
#define MAP_MATCHING_HPP

#include "engine/algorithm.hpp"
#include "engine/datafacade/contiguous_internalmem_datafacade.hpp"
#include "engine/map_matching/sub_matching.hpp"
#include "engine/search_engine_data.hpp"

#include <vector>

namespace osrm
{
namespace engine
{
namespace routing_algorithms
{

using CandidateList = std::vector<PhantomNodeWithDistance>;
using CandidateLists = std::vector<CandidateList>;
using SubMatchingList = std::vector<map_matching::SubMatching>;
static const constexpr double DEFAULT_GPS_PRECISION = 5;

//[1] "Hidden Markov Map Matching Through Noise and Sparseness";
//     P. Newson and J. Krumm; 2009; ACM GIS
SubMatchingList
mapMatching(SearchEngineData &engine_working_data,
            const datafacade::ContiguousInternalMemoryDataFacade<algorithm::CH> &facade,
            const CandidateLists &candidates_list,
            const std::vector<util::Coordinate> &trace_coordinates,
            const std::vector<unsigned> &trace_timestamps,
            const std::vector<boost::optional<double>> &trace_gps_precision,
            const bool allow_splitting);

SubMatchingList
mapMatching(SearchEngineData &engine_working_data,
            const datafacade::ContiguousInternalMemoryDataFacade<algorithm::CoreCH> &facade,
            const CandidateLists &candidates_list,
            const std::vector<util::Coordinate> &trace_coordinates,
            const std::vector<unsigned> &trace_timestamps,
            const std::vector<boost::optional<double>> &trace_gps_precision,
            const bool allow_splitting);
}
}
}

#endif /* MAP_MATCHING_HPP */
