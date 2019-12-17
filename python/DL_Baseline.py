import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
import keras
import json
from tqdm.auto import tqdm
import warnings
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV
from keras.models import Sequential
from keras.layers import Dense
from keras.wrappers.scikit_learn import KerasClassifier

try:
    from common import pandas_to_spark
except:
    from python.common import pandas_to_spark

def DL_Model(train, test=None, flag=None, plot=False) :

	if flag == None :
		train = train[['user_id', 'business_id','rating']]
		test = test[['user_id','business_id','rating']]
		X = train[['user_id','business_id']]
		y = train['rating']

	elif flag == "Business" :
		train = train[['user_id', 'business_id', 'longitude', 'latitude', 'stars',
		   'review_count', 'is_open','rating']]
		test = test[['user_id','business_id','longitude', 'latitude' ,'stars','review_count','is_open','rating']]
		X = train[['user_id','business_id','longitude', 'latitude' ,'stars','review_count','is_open']]
		y = train['rating']


	elif flag == "Both" :
		train = train.drop(columns=[ "date" ,"name_x" , "address","city" ,"state" ,"postal_code" ,"text","name_y" ,"elite","yelping_since"],axis=1)
		test = test.drop(
		columns=["date", "name_x", "address", "city", "state",
		         "postal_code", "text", "name_y", "elite",
		         "yelping_since"], axis=1)
		y = train["rating"]
		X = train.drop(columns=["rating"],axis=1)

	le1= LabelEncoder()
	le2 = LabelEncoder()
	X.fillna(0,inplace=True)
	X['user_id'] = le1.fit_transform(X['user_id'])
	X['business_id'] = le2.fit_transform(X['business_id'])

	model = KerasClassifier(build_fn=create_model, verbose=0)
	# define the grid search parameters
	batch_size = [128, 246, 512, 1024]
	epochs = [1,3,6,10]
	optimizer = ['SGD', 'RMSprop', 'Adam']
	learn_rate = [0.001, 0.001,0.1, 1]
	param_grid = {'epochs':[1]}#dict(batch_size=batch_size, epochs=epochs, optimizer=optimizer)
	grid = GridSearchCV(estimator=model, param_grid=param_grid, n_jobs=-1, cv=3,verbose=3)
	grid_result = grid.fit(X, y)
	# summarize results
	print("Best: %f using %s" % (grid_result.best_score_, grid_result.best_params_))
	means = grid_result.cv_results_['mean_test_score']
	stds = grid_result.cv_results_['std_test_score']
	params = grid_result.cv_results_['params']
	for mean, stdev, param in zip(means, stds, params):
		print("%f (%f) with: %r" % (mean, stdev, param))

	if plot:
		plt.plot(hist.history['loss'])
		plt.plot(hist.history['val_loss'])
		plt.title('model loss')
		plt.ylabel('loss')
		plt.xlabel('epoch')
		plt.legend(['train', 'test'], loc='upper left')
		plt.show()


	test['user_id'] = le1.transform(test['user_id'])
	test['business_id'] = le2.transform(test['business_id'])
	preds = test[['user_id', 'business_id','rating']]
	preds['predictions'] = np.clip(model.predict(test.drop('rating',axis=1)), a_min=1, a_max=5)
	#print(preds.head())

	train['user_id'] = le1.transform(train['user_id'])
	train['business_id'] = le2.transform(train['business_id'])
	train_ret = train[['user_id','business_id','rating']]
	#train_ret['predictions'] = np.clip(model.predict(train.drop('rating', axis=1)), a_min=1,a_max=5)
	#print(train_ret.head())

	preds_spark = pandas_to_spark(preds)
	train_spark = pandas_to_spark(train_ret)
	test_spark = pandas_to_spark(preds[['user_id','business_id','rating']])

	#print(train_spark)
	#print(test_spark)
	#print(preds_spark)
	return(train_spark, test_spark, preds_spark)


def create_model():
# create model
	model = keras.Sequential()
	model.add(keras.layers.Dense(16, input_dim=2, activation='relu'))
	model.add(keras.layers.Dense(8, activation='relu'))
	model.add(keras.layers.Dense(16, activation='relu'))
	model.add(keras.layers.Dense(1, activation=None))

	model.compile(loss='mse', optimizer='adam', metrics=['mse','accuracy'])
	#hist = model.fit(X,y, batch_size=1024,epochs=1, validation_split=0.3)


	return model 



if __name__=='__main__':
    warnings.simplefilter('ignore')
    df = pd.read_csv('../data/ratings.csv')
    DL_Model(df,df,None)