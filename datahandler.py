
import pandas as pd
import os
# first API volumn is bs...
#How to store

location=os.getcwd()
location=location+'/Currency/'
#path = r"/Users/yulanda/Documents/Study/MFE/2015-2016/FE5110 project/TrendFollowing/TrendFollowing/"
path=location
print path

#import pandas.io.data as web       -- for older version of pandas, mengdan is using this
#import pandas.io.data.DataReader as dr
import pandas_datareader. data as web   # for new pandas version, i am using version 0.19.2 so need to import this


listOfCur =  ['JPY','CAD','EUR','GBP','CHF','SGD','INR','MXN','AUD','NZD']
#'EUR','GBP','CHF','SGD','INR','MXN','AUD','NZD'
historicalCur = {}
for cur in listOfCur:
    historicalCur[cur] = web.DataReader(cur+'=X','yahoo')
    #historicalCur[cur].iloc[::-1]
    historicalCur[cur].to_csv(path+'/'+cur+'.csv',sep=',')





