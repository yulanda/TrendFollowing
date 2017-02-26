import pandas as pd
import matplotlib.pyplot as plt
import plotly
from plotly import tools
plotly.tools.set_credentials_file(username='federicka', api_key='JCD1oaDrczp1szQ1xWfV')
import plotly.graph_objs as go
import plotly.plotly as py
import numpy as np


data = pd.read_csv(r"/Users/mengdantian/Desktop/quantitative strategy/trend/AUDMAbuysellwBand.csv")

def rolling_plot(df, index_roll):
    index_nd = df.index[-1]
    index_st = 0

    while index_st + index_roll < index_nd:
        print index_st
        series = df['CumulativeMAbuysellwBand5PnL']
        ts = series[index_st:index_st+index_roll]
        plt.plot(ts)
        plt.figure()
        plt.show()
        index_st = index_st + index_roll
    else:
        print "plot all rolling window available"


#rolling_plot(data, 800)

def rolling_plot_allinone(df, index_roll,name, underlying_name):
    index_nd = df.index[-1]
    index_st = 0
    plt_num = index_nd / index_roll
    #assert type(name) == "str"
    series = df[name]
    ts_index = df['Date']
    fig = tools.make_subplots(rows=plt_num / 2 if plt_num % 2 == 0 else (plt_num / 2 + 1), cols=2)#subplot_titles=(, 'Plot 2',
    for i in range(1,(plt_num+1)):
        j = 2 if i % 2 == 0 else 1
        print i
        print j
        #print index_st
        ts = go.Scatter(x = ts_index[index_st:index_st+index_roll],y = series[index_st:index_st+index_roll])
        fig.append_trace(ts,(i-j)/2+1,j)
        index_st = index_st + index_roll
    else:
        print "plot all rolling window available"

    fig['layout'].update(height=1000, width=1200, title= 'plot of ' + name)


    plot_url = py.plot(fig, filename=underlying_name+name+'_plot')
    py.image.save_as(fig, filename=underlying_name+name+'_plot.png')
    return plot_url


rolling_plot_allinone(data, 400,'CumulativeMAbuysellwBand5PnL','AUD')