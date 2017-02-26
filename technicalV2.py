import pandas as pd
import numpy as np
import csv
import os
from datetime import date, timedelta

# fUNCTIONS OBJECTIVE: calculate sma based on different windows and write csv, update new sma for new data coming and
#update corresponding csv, kept only the most recently csv for indicator
result = pd.DataFrame

import pandas as pd
df = pd.DataFrame({'strategy': ['simpleMAbuysell','MAbuysellwBand'], 'techIndNames':[[('sma5d'),('sma10d'),('sma15d'),('sma20d'),('sma30d'),('sma45d')],
[('sma5d','bolligerband5d'),('sma10d','bolligerband10d'),('sma15d','bolligerband15d'),('sma20d','bolligerband20d'),
 ('sma30d', 'bolligerband30d'), ('sma45d', 'bolligerband45d')]]})
#df.to_csv('strategy_techIndnew.csv')
technical_inds = df

def sma(pn_data, index, window):
    return np.mean(pn_data[index- window: index]['Adj Close'])

def bolligerband(pn_data, index, window):
    return np.std(pn_data[index- window: index]['Adj Close'])

def isNaN(x):
    return str(float(x)).lower() == 'nan'   #.contains("nan")

def simpleMAbuysell(pn_data, index, strategy_tuple):

    #assert type(strategy_tuple) == 'str'
    #return np.where(pn_data[index:index]['Adj Close'] > pn_data[index:index][IndName],1,-1)
    if pn_data['Adj Close'][index] > pn_data[strategy_tuple][index]:
        return 1
    else:
        return -1

def MAbuysellwBand(pn_data, index,strategy_tuple):

    #assert type(strategy_tuple[0]) == 'str'
    if pn_data['Adj Close'][index] > pn_data[strategy_tuple[0]][index] + 2.5 * pn_data[strategy_tuple[1]][index]:
        return -1
    elif pn_data['Adj Close'][index] > pn_data[strategy_tuple[0]][index] + pn_data[strategy_tuple[1]][index]:
        return 1
    elif pn_data['Adj Close'][index] < pn_data[strategy_tuple[0]][index] - 2.5 * pn_data[strategy_tuple[1]][index]:
        return 1
    else:
        return -1



def profitloss(result, signalGenerator, underlying, id):

    result['new'+ signalGenerator+str(id)+'PnL'] = [0] * len(result)
    result['old'+ signalGenerator+str(id)+'PnL'] = [0] * len(result)
    # calculate new p&l based on the buy sell strategy
    for i in result.index:
        # Open position keep track of my cumulative open profolio
        OpenPositionCount = 'OpenPosition' + signalGenerator + str(id)
        if i > 0:  # make sure start from row 1 (skip row 0)

            if (not isNaN(result[OpenPositionCount][i])) and (not isNaN(result[OpenPositionCount][i - 1])):
                # same sign: abs today's count is smaller than yesterday's count -> closeout
                if ((result[OpenPositionCount][i] >= 0 and (result[OpenPositionCount][i - 1] >= 0
                                                            or result[OpenPositionCount][i] is None)) or
                        (result[OpenPositionCount][i] < 0 and (result[OpenPositionCount][i - 1] < 0
                                                               or result[OpenPositionCount][i] is None))):
                    if (abs(result[OpenPositionCount][i]) > abs(result[OpenPositionCount][i - 1])):
                        result.loc[i, 'new'+ signalGenerator + str(id)+'PnL'] = (result['Adj Close'][i] - result['Open'][i]) * \
                                                      result['BuySell'+ signalGenerator + str(id)][i]
                        result.loc[i, 'old'+ signalGenerator + str(id)+'PnL'] = (result['Adj Close'][i] - result['Adj Close'][i - 1]) * \
                                                                result[OpenPositionCount][i]
                        # same sign: abs today's count is greater than yesterday's count -> open
                    else:
                        result.loc[i, 'new'+ signalGenerator + str(id)+'PnL'] = (result['Open'][i] - result['Adj Close'][i - 1]) * \
                                                      result['BuySell'+signalGenerator + str(id)][i]
                        result.loc[i, 'old'+ signalGenerator + str(id)+ 'PnL'] = (result['Adj Close'][i] - result['Adj Close'][i - 1]) * \
                                                                result[OpenPositionCount][i - 1]
                # different sign:  close out yesterday's position + open today's abs position
                elif ((result[OpenPositionCount][i] >= 0 and result[OpenPositionCount][i - 1] < 0)
                      or (result[OpenPositionCount][i] < 0 and result[OpenPositionCount][i - 1] > 0)):
                    if result[OpenPositionCount][i] >= 0:
                        result.loc[i, 'new'+ signalGenerator + str(id)+'PnL'] = (result[OpenPositionCount][i] * (
                        result['Adj Close'][i] - result['Open'][i]) \
                                                       + result[OpenPositionCount][i - 1] * (
                                                       result['Open'][i] - result['Adj Close'][i - 1])) \
                                                      * result['BuySell'+signalGenerator + str(id)][i]
                        result.loc[i, 'old'+ signalGenerator + str(id)+'PnL'] = (result[OpenPositionCount][i] * (
                            result['Adj Close'][i] - result['Open'][i])
                                                                 + result[OpenPositionCount][i - 1] *
                                                                 (result['Open'][i] - result['Adj Close'][i - 1])) * \
                                                                result['BuySell'+signalGenerator + str(id)][i]

    # calculate daily P&L
    result['TodayTotal'+signalGenerator + str(id)+'PnL'] = result['old'+signalGenerator + str(id)+'PnL'] + result['new'+signalGenerator + str(id)+'PnL']
    # calculate cumulative P&L
    result['Cumulative'+signalGenerator + str(id)+'PnL'] = result['TodayTotal'+signalGenerator + str(id)+'PnL'].cumsum()
    return result


def historicalTechnical(underlying, signalGenerator):
    #read FX rates from cvs and put it to underlyingdata as DataFrame
    underlyingData = pd.read_csv(underlying+'.csv')
    UD = underlyingData.set_index(['Date'])
    #create Dataframe for sma
    technicalpd = pd.DataFrame(index=underlyingData['Date'])
    obs = len(underlyingData)
    #get the technical indicator names list from the csv by strategy name first
    techIndlist = technical_inds.loc[technical_inds['strategy'] == signalGenerator]['techIndNames']

    for i, val in enumerate(techIndlist.values[0]):  # this one seems coz its a core series, always need [0] to get the list

        if(type(val) is str):
            day = int(filter(str.isdigit, val))
            techIndName = val.replace(str(day)+'d','')
            technicalpd.loc[day:,val]= list(globals()[techIndName](underlyingData, index, day) for index in xrange(day, obs))
        elif(type(val) is tuple):
            for j in range(len(val)):
                day = int(filter(str.isdigit, val[j]))
                techIndName = val[j].replace(str(day) + 'd', '')
                technicalpd.loc[day:, val[j]] = list(globals()[techIndName](underlyingData, index, day) for index in xrange(day, obs))
        else:
             print "other situation for technical indicators"

    lastDate = technicalpd.index[-1]
    combineRate = [UD, technicalpd]
    technicalpd.to_csv(techIndName + underlying + lastDate + '.csv')
    result = pd.concat(combineRate, axis=1)
    result.reset_index(level=0, inplace=True)

    for i, val in enumerate(techIndlist.values[0]):
        Buysellcolumn = 'BuySell' + signalGenerator + str(i)
        OpenPositionCount = 'OpenPosition' + signalGenerator + str(i)
        if (type(val) is str):
            day = int(filter(str.isdigit, val))
        elif (type(val) is tuple):
            for j in range(len(val)):
                day = int(filter(str.isdigit, val[j]))

        result.loc[day:, Buysellcolumn] = list(globals()[signalGenerator](result, index, val) for index in xrange(day, obs))
        # calculate cumulative open positions and add to a new column
        result[OpenPositionCount] = result[Buysellcolumn].cumsum()
        print "hey"
        profitloss(result, signalGenerator, underlying, i)

    result.to_csv(underlying + signalGenerator + '.csv')
    return result



    #decide buy or sell based on the adjusted close price and the sma for different sma window (5,10,15,20,30,45 days)
    #1 means buy and -1 means sell
    #calculate cumulative openPositin for the asset
    
    #profitloss(result, str(techIndName), day, underlying)
    #output result file with rate/sma/buysell indicator/open position/new p&l/old p&l to cvs
    #result.to_csv(techIndName + underlying + lastDate + '.csv')



####cant work because I add one more feature Bolligerband, so that the technical column and open position col cant work

historicalTechnical('AUD', 'simpleMAbuysell') # get the historical up to date sma
historicalTechnical('AUD', 'MAbuysellwBand')
'''historicalTechnical([5,10,15,20,30,45], 'sma','CAD') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','CHF') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','EUR') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','GBP') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','INR') # sget the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','JPY') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','MXN') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','NZD') # get the historical up to date sma
historicalTechnical([5,10,15,20,30,45], 'sma','SGD') # get the historical up to date sma'''

#update function and csv file
def updateTechnical(listofdays, techIndName, underlying, currentDate,lastDate):

    underlyingData = pd.read_csv(underlying + '.csv')
    try:
        underlyingData.index[-1] == currentDate #check if the lastline of original data is the currentdate
        smanew =  [sma(underlyingData,len(underlyingData), day) for day in listofdays] #new sma for the current rate only
        newrow = [currentDate]
        newrow.extend(smanew) #write it to a list of string for the appending row for csc
        try:
            if os.path.exists(techIndName + underlying + currentDate + '.csv'):
                print "check if technical indicator it is alrady up to date"
        except:
            if not os.path.exists(techIndName + underlying + lastDate + '.csv'): # check if the lastdate.csv exists
                file(techIndName + underlying + lastDate + '.csv', 'w').close()
                print "pls check if the lastdate technicalindicator csv is here"
            else:#update a new row with current date indicators
                with open(techIndName + underlying + lastDate + '.csv', 'a') as f:
                    print f
                    writer = csv.writer(f)
                    writer.writerow(newrow)
                os.rename(techIndName + underlying + lastDate + '.csv', techIndName + underlying + currentDate + '.csv')#update csv name
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