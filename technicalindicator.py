import pandas as pd
import numpy as np
import csv
import os
from datetime import date, timedelta

# fUNCTIONS OBJECTIVE: calculate sma based on different windows and write csv, update new sma for new data coming and
#update corresponding csv, kept only the most recently csv for indicator
ccylocation = os.getcwd() + '/Currency/'
result = pd.DataFrame

def sma(pn_data, index, window):
    return np.mean(pn_data[index- window: index]['Adj Close'])

def isNaN(x):
    return str(float(x)).lower() == 'nan'   #.contains("nan")

def buysell(pn_data, index, IndName):
    #return np.where(pn_data[index:index]['Adj Close'] > pn_data[index:index][IndName],1,-1)
    if pn_data['Adj Close'][index] > pn_data[IndName][index]:
        return 1
    else:
        return -1

def historicalTechnical(listofdays, techIndName,underlying):
    #read FX rates from cvs and put it to underlyingdata as DataFrame
    underlyingData = pd.read_csv(ccylocation+underlying+'.csv')
    UD = underlyingData.set_index(['Date'])
    #create Dataframe for sma
    technicalpd = pd.DataFrame(index=underlyingData['Date'])
    obs = len(underlyingData)
    #populate sma data for all dates for different sma window (5,10,15,20,30,45 days)
    for day in listofdays:
        technicalpd.loc[day:,techIndName+str(day)+'d']= list(sma(underlyingData, index, day) for index in xrange(day, obs))

    lastDate = technicalpd.index[-1]
    #technicalpd.to_csv(ccylocation+techIndName + underlying + lastDate + '.csv')
    combineRateSMA = [UD, technicalpd]
    result = pd.concat(combineRateSMA, axis=1)

    #decide buy or sell based on the adjusted close price and the sma for different sma window (5,10,15,20,30,45 days)
    #1 means buy and -1 means sell
    #calculate cumulative openPositin for the asset
    result.reset_index(level=0, inplace=True)
    for day in listofdays:
        techIndColumn=techIndName+str(day)+'d'
        Buysellcolumn = 'BuySell'+ techIndColumn
        OpenPositionCount = 'OpenPosition' + techIndColumn
        result.loc[day:, Buysellcolumn] = list(buysell(result, index, techIndColumn) for index in xrange(day, obs))
        # calculate cumulative open positions and add to a new column
        result[OpenPositionCount] = result[Buysellcolumn].cumsum()

    result['newsma5PnL'] = [0] * len(result)
    #calculate new p&l based on the buy sell strategy
    for i in result.index:
        #Open position keep track of my cumulative open profolio
        OpenPositionCount='OpenPosition'+ techIndName + '5d'
        if i>0: #make sure start from row 1 (skip row 0)
            if (not isNaN(result[OpenPositionCount][i])) and (not isNaN(result[OpenPositionCount][i-1])):
                #same sign: abs today's count is smaller than yesterday's count -> closeout
                if ((result[OpenPositionCount][i]>=0 and (result[OpenPositionCount][i-1]>=0
                                                           or result[OpenPositionCount][i] is None)) or
                    (result[OpenPositionCount][i]<0 and (result[OpenPositionCount][i-1]<0
                                                           or result[OpenPositionCount][i] is None))):
                    if (abs(result[OpenPositionCount][i])>abs(result[OpenPositionCount][i-1])):
                        result.loc[i,'newsma5PnL'] = (result['Adj Close'][i] - result['Open'][i])*result['BuySellsma5d'][i]
                        #same sign: abs today's count is greater than yesterday's count -> open
                    else:
                        result.loc[i,'newsma5PnL']=(result['Open'][i] - result['Adj Close'][i-1])*result['BuySellsma5d'][i]
                #different sign:  close out yesterday's position + open today's abs position
                elif ((result[OpenPositionCount][i]>=0 and result[OpenPositionCount][i-1]<0)
                      or (result[OpenPositionCount][i]<0 and result[OpenPositionCount][i-1]>0)):
                    if result[OpenPositionCount][i]>=0:
                        result.loc[i, 'newsma5PnL'] = (result[OpenPositionCount][i]*(result['Adj Close'][i] - result['Open'][i]) \
                                                     + result[OpenPositionCount][i-1]*(result['Open'][i] - result['Adj Close'][i-1])) \
                                                     * result['BuySellsma5d'][i]
    result['oldsma5PnL'] = [0] * len(result)
    # calculate old p&l
    for i in result.index:
        OpenPositionCount = 'OpenPosition' + techIndName + '5d'
        if i>0: #make sure start from row 1 (skip row 0)
            if (not isNaN(result[OpenPositionCount][i])) and (not isNaN(result[OpenPositionCount][i-1])):
                # same sign: abs today's count is smaller than yesterday's count -> closed off partial position from yesterday
                if ((result[OpenPositionCount][i]>=0 and (result[OpenPositionCount][i-1]>=0
                                                           or result[OpenPositionCount][i] is None)) or
                    (result[OpenPositionCount][i]<0 and (result[OpenPositionCount][i-1]<0
                                                           or result[OpenPositionCount][i] is None))):
                    if (abs(result[OpenPositionCount][i])>abs(result[OpenPositionCount][i-1])):
                        result.loc[i, 'oldsma5PnL'] = (result['Adj Close'][i] - result['Adj Close'][i-1]) * result[OpenPositionCount][i]
                    else:
                        #same sign: abs today's count is greater than yesterday's count -> open more position
                        result.loc[i, 'oldsma5PnL'] = (result['Adj Close'][i] - result['Adj Close'][i - 1]) * result[OpenPositionCount][i-1]
                # different sign:  closed out all yesterday's position
                elif ((result[OpenPositionCount][i]>=0 and result[OpenPositionCount][i-1]<0)
                      or (result[OpenPositionCount][i]<0 and result[OpenPositionCount][i-1]>0)):
                    if result[OpenPositionCount][i]>=0:
                        result.loc[i, 'oldsma5PnL'] = (result[OpenPositionCount][i] * (result['Adj Close'][i] - result['Open'][i])
                                                       + result[OpenPositionCount][i-1] *
                                                       (result['Open'][i] - result['Adj Close'][i-1])) * result['BuySellsma5d'][i]

    #calculate daily P&L
    result['TodayTotalPnL'] = result['oldsma5PnL']+result['newsma5PnL']
    #calculate cumulative P&L
    result['CumulativePnL'] = result['TodayTotalPnL'].cumsum()

    #output result file with rate/sma/buysell indicator/open position/new p&l/old p&l to cvs
    result.to_csv(ccylocation+techIndName + underlying + lastDate + '.csv')




historicalTechnical([5,10,15,20,30,45], 'sma','AUD') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','CAD') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','CHF') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','EUR') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','GBP') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','INR') # sget the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','JPY') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','MXN') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','NZD') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','SGD') # get the historical up to date sma

#update function and csv file
def updateTechnical(listofdays, techIndName, underlying, currentDate,lastDate):

    underlyingData = pd.read_csv(ccylocation+underlying + '.csv')
    try:
        underlyingData.index[-1] == currentDate #check if the lastline of original data is the currentdate
        smanew =  [sma(underlyingData,len(underlyingData), day) for day in listofdays] #new sma for the current rate only
        newrow = [currentDate]
        newrow.extend(smanew) #write it to a list of string for the appending row for csc
        try:
            if os.path.exists(ccylocation+techIndName + underlying + currentDate + '.csv'):
                print "check if technical indicator it is alrady up to date"
        except:
            if not os.path.exists(ccylocation+techIndName + underlying + lastDate + '.csv'): # check if the lastdate.csv exists
                file(ccylocation+techIndName + underlying + lastDate + '.csv', 'w').close()
                print "pls check if the lastdate technicalindicator csv is here"
            else:#update a new row with current date indicators
                with open(ccylocation+techIndName + underlying + lastDate + '.csv', 'a') as f:
                    print f
                    writer =  csv.writer(f)
                    writer.writerow(newrow)
                os.rename(ccylocation+techIndName + underlying + lastDate + '.csv', techIndName + underlying + currentDate + '.csv')#update csv name
    except:
        print "pls check the new original data is up to date"


updateTechnical([5,10,15,20,30,45], 'sma','AUD',date.today(),date.today() - timedelta(1))
updateTechnical([5,10,15,20,30,45], 'sma','CAD',date.today(),date.today() - timedelta(1))
updateTechnical([5,10,15,20,30,45], 'sma','CHF',date.today(),date.today() - timedelta(1))
updateTechnical([5,10,15,20,30,45], 'sma','EUR',date.today(),date.today() - timedelta(1))
updateTechnical([5,10,15,20,30,45], 'sma','GBP',date.today(),date.today() - timedelta(1))
updateTechnical([5,10,15,20,30,45], 'sma','INR',date.today(),date.today() - timedelta(1))
updateTechnical([5,10,15,20,30,45], 'sma','JPY',date.today(),date.today() - timedelta(1))
updateTechnical([5,10,15,20,30,45], 'sma','MXN',date.today(),date.today() - timedelta(1))
updateTechnical([5,10,15,20,30,45], 'sma','NZD',date.today(),date.today() - timedelta(1))
updateTechnical([5,10,15,20,30,45], 'sma','SGD',date.today(),date.today() - timedelta(1))