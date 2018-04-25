Splitting Datasets into Training/Testing/Validating 
---------------------------------------------------

This example shows how to split a single dataset into two datasets, one used for training and the other used for testing. 

Note that when splitting frames, H2O does not give an exact split. It's designed to be efficient on big data using a probabilistic splitting method rather than an exact split. For example, when specifying a 0.75/0.25 split, H2O will produce a test/train split with an expected value of 0.75/0.25 rather than exactly 0.75/0.25. On small datasets, the sizes of the resulting splits will deviate from the expected value more than on big data, where they will be very close to exact.

.. example-code::
   .. code-block:: r
   
	> library(h2o)
	> h2o.init(nthreads=-1)
	
	# Import the prostate dataset
	> prostate.hex <- h2o.importFile(path = "https://raw.github.com/h2oai/h2o/master/smalldata/logreg/prostate.csv", destination_frame = "prostate.hex")
	
	# Split dataset giving the training dataset 75% of the data
	> prostate.split <- h2o.splitFrame(data=prostate.hex, ratios=0.75)
	
	# Create a training set from the 1st dataset in the split
	> prostate.train <- prostate.split[[1]]
	
	# Create a testing set from the 2nd dataset in the split
	> prostate.test <- prostate.split[[2]]
	
	# Generate a GLM model using the training dataset. x represesnts the predictor column, and y represents the target index.
	> prostate.glm <- h2o.glm(y = "CAPSULE", x = c("AGE", "RACE", "PSA", "DCAPS"), training_frame=prostate.train, family="binomial", nfolds=10, alpha=0.5)
	
	# Predict using the GLM model and the testing dataset
	> pred = h2o.predict(object=prostate.glm, newdata=prostate.test)
	
	# View a summary of the prediction with a probability of TRUE
	> summary(pred$p1, exact_quantiles=TRUE)
	p1
	Min.   :0.2044
	1st Qu.:0.2946
	Median :0.3369
	Mean   :0.3928
	3rd Qu.:0.4258
	Max.   :0.9124 

   .. code-block:: python

	>>> import h2o
	>>> from h2o.estimators.glm import H2OGeneralizedLinearEstimator
	>>> h2o.init()
	
	# Import the prostate dataset
	>>> prostate = "https://raw.github.com/h2oai/h2o/master/smalldata/logreg/prostate.csv"
	>>> prostate_df = h2o.import_file(path=prostate)
	
	# Split the data into Train/Test/Validation with Train having 70% and test and validation 15% each
	>>> train,test,valid = prostate_df.split_frame(ratios=(.7, .15))
	
	# Generate a GLM model using the training dataset
	>>> glm_classifier = H2OGeneralizedLinearEstimator(family="binomial", nfolds=10, alpha=0.5)
	>>> glm_classifier.train(y="CAPSULE", x=["AGE", "RACE", "PSA", "DCAPS"], training_frame=train)
	
	# Predict using the GLM model and the testing dataset
	>>> predict = glm_classifier.predict(test)
	
	# View a summary of the prediction
	>>> predict.head()
	  predict         p0        p1
	---------  ---------  --------
    		0  0.733779   0.266221
        	1  0.314968   0.685032
	        1  0.0899778  0.910022
	        1  0.146287   0.853713
	        1  0.648841   0.351159
	        0  0.83804    0.16196
	        1  0.623304   0.376696
	        1  0.597705   0.402295
	        0  0.757942   0.242058
	        1  0.654244   0.345756
	
	[10 rows x 3 columns]
