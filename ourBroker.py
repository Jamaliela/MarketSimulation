from Tariff import Tariff
import random
import csv
import pandas as pd
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
import math


class BrokerOurs:

    def __init__(self, idx):

        # ID number, cash balance, energy balance
        self.idx = idx
        self.cash = 0
        self.power = 0
        self.customer_usage = None
        self.other_data = None
        self.tariff_monitor = []

        # Lists to contain:
        # asks: tuples of the form ( quantity, price )
        # tariffs: Tariff objects to submit to the market
        # customers: integers representing which customers are subscribed
        # to your tariffs.
        self.asks = []
        self.tariffs = []
        self.customers = []
        self.price=[]
        self.av=[]


    # A function to accept the bootstrap data set.  The data set contains:
    # usage_data, a dict in which keys are integer customer ID numbers,
    # and values are lists of customer's past usage profiles.
    # other_data, a dict in which 'Total Demand' is a list of past aggregate demand
    # figures, 'Cleared Price' is a list of past wholesale prices,
    # 'Cleared Quantity' is a list of past wholesale quantities,
    # and 'Difference' is a list of differences between cleared
    # quantities and actual usage.

    def get_initial_data(self, usage_data, other_data):

        self.customer_usage = usage_data
        self.other_data = other_data



    def simulation_price(self):
        """
        by using normal distribution and the Cleared Price column in the file otherdata.csv we calculate
        the our prices"
        """
        # style.use('ggplot')
        prices= self.other_data["Cleared Price"]
        mean= np.mean(prices, dtype=np.float64)
        # print(mean)
        series = pd.Series(np.array(prices))
        # print(series)
        # how much the prices given time. in this case each hour
        returns= series.pct_change()
        # print(returns)

        #last price of the cleared prices
        last_price= self.other_data["Cleared Price"][-1] # opening file
        min_cleared_price= min(prices)  # calculating the min of the prices

        num_simulations = 1000 # setting amount of simulations
        num_hours = 335 # number of hours of data (two weeks of data)
        simulation_df = pd.DataFrame()
        for x in range(num_simulations): # running the simulations
            count = 0
            hourly_vol = returns.std() # the hourly volume will be the standard deviation

            predicted_prices = []
            price = last_price * (1 + np.random.normal(0, hourly_vol)) # setting each price to random numbers according to the normal distribution

            predicted_prices.append(round(price, 0)) # putting all the prices in one string and rounding them

            for y in range(num_hours):
                if count == 334:
                    break
                #normal distributions here
                price = predicted_prices[count] * (1 + np.random.normal(0, hourly_vol)) # making the predicted prices have a normal distribution
                predicted_prices.append(price) #a
                count += 1
            simulation_df[x] = predicted_prices
            # result_prices=[]
            for i in range(len(predicted_prices)):
                if predicted_prices[i] < min_cleared_price: # condition that ensures that all the prices are positive (bigger than the min_cleared price
                    continue
                else:
                    self.price.append(predicted_prices[i])
        self.price=[round(i) for i in self.price]

    def quantity_calculations(self):
        """
        This function calculates the quantity for the demand"
        """
        df = pd.DataFrame(pd.read_csv("CustomerNums.csv",index_col=0,header=0)) # accessing the document
        # print(df)
        av=[]
        for i in range(336):
            av.append(df[str(i)].mean()*100 - self.power) # applying the formula to calculate average.
        # print(str(av) + "\n")
        self.av=[round(i) for i in av] # rounding our result

    # Returns a list of asks of the form ( price, quantity ).
    def post_asks(self, time):
        """
        this function uses the two functions above to post the asks
        :return: returns a list of asks of the form ( price, quantity ).
        """
        # calling our two functions first
        self.simulation_price()
        self.quantity_calculations()
        # calculating the demand and price % 23 to see which interval they fall in
        demand_post= self.av[time%23]
        price_post= self.price[time%23]

        # posting them in a tuple
        asks= ([(price_post, demand_post) for i in range(0, 1)])
        print(asks)

        return asks

    # Returns a list of Tariff objects
    def post_tariffs(self, time):
        """
        This function will post the tarrifs according to the duration, exitfee and prices.
        :return: Returns a list of Tariff objects
        """
        # initializing variables
        ret=[]
        predicted= list(map(int, self.price))

        for i in predicted:  # looping the tarrifs to calculate the average, exit fee and predicted prices
            predicted= round(i*1.4, 0)
        average= list(map(int, self.av))
        calculated_exit_fee=predicted *average[time % 23] * 0.1 / len(self.customer_usage)
        self.exitfee =calculated_exit_fee
        self.tariff_price = predicted

        # returning each iteration of the tarrifs
        ret.append(Tariff( self.idx, price=self.tariff_price, duration=3, exitfee=self.exitfee))

        return ret

    def receive_message(self, msg):
        """
        Receives data for the last time period from the server.
        """
        # calculating the new amount of customers so that it can get printed
        cx_updated = len(self.customers) - len(self.customers)
        current_name_of_custo = len(self.customers) - cx_updated

        tariffs = msg["Tariffs"]

        # setting up format so that each iteration is printed
        for t in tariffs:
            print ("price: {} Duration: {} exitfee: {} number_of_customers: {} "
            .format(round(t.price), round(t.duration), round(t.exitfee), current_name_of_custo))


    # Returns a negative number if the broker doesn't have enough energy to
    # meet demand.  Returns a positive number otherwise.
    def get_energy_imbalance( self, data ):
        return self.power

    def gain_revenue( self, customers, data ):
        for c in self.customers:
            self.cash += data[c] * customers[c].tariff.price
            self.power -= data[c]

    ## Alter broker's cash balance based on supply/demand match.
    def adjust_cash( self, amt ):
        self.cash += amt
