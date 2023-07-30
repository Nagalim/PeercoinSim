import numpy as np
import matplotlib.pyplot as plt
import csv

plt.rcParams['figure.figsize'] = [6.0, 5.0]
MAX_DAYS = 365*2
MIN_PROB_DAYS= 30
RAMP_UP = 60
RELATIVE_REWARD = 0.03
DIFF = 17
STATIC_REWARD = 1.34
EXAMPLE_SIZE = 80
MAX_COINAGE = 365
SUPPLY = 28282491
BLOCKTIME = 10*60

#1/(SUPPLY*averageMints(40, 17)/(BLOCKYEAR))
#averageMints(100,16.3248)/averageMints(40, 20)

SECDAY=60*60*24
DAYYEAR=(365*33+8)/33
# Offset days by 0.5 to assume mint occurs somewhere in middle of day
DAYS = [MIN_PROB_DAYS+x+0.5 for x in range(MAX_DAYS)]
DAYS_WITH_NO_MINT = DAYS + [MAX_DAYS+MIN_PROB_DAYS]
BLOCKYEAR=DAYYEAR*SECDAY/BLOCKTIME

# 60.5/(RAMP_UP+0.5) normalises so that the end probability is always the same
# Offset by 0.5 to assume middle of day
probSecs = np.array([2**224 * (min(x, RAMP_UP)+0.5) * (60.5/(RAMP_UP+0.5)) / (2**256) for x in range(MAX_DAYS)])

def generateDailyProbs(outValue, diff):
    
    adj = outValue / diff

    # Independent probabilities
    failDayProbs = (1 - probSecs*adj)**SECDAY
    mintDayProbs = 1 - failDayProbs

    # Actual probability of mint on day assuming no mints before
    cumFail = failDayProbs.cumprod()
    # Prob of fail up-to now
    cumPrevFail = np.insert(cumFail, 0, 1)[:MAX_DAYS]
    # Prob of fail up-to now and success now gives chance of mint on this day
    # Add probabilty of final day to represent no successful mints
    return np.append(cumPrevFail*mintDayProbs, cumFail[-1])

dayProbs = generateDailyProbs(EXAMPLE_SIZE, DIFF)

def dailyRewards(outValue, staticReward):
    mintRewards = np.fromiter((outValue*RELATIVE_REWARD*min(MAX_COINAGE, x)/DAYYEAR + staticReward for x in DAYS), dtype=float)
    includingFailed = np.append(mintRewards, 0)
    return includingFailed

def averageReward(outValue, diff, staticReward):
    probs = generateDailyProbs(outValue, diff)
    rewards = dailyRewards(outValue, staticReward)
    returns = 1+rewards/outValue
    
    weightedReturn = (returns**probs).prod()
    weightedTime = (DAYS_WITH_NO_MINT*probs).sum()
    return (weightedReturn**(DAYYEAR/weightedTime) - 1) * 100

sizes = [10**(x/125)/100 for x in range(1000)]

rewardForSizes = np.fromiter((averageReward(x, DIFF, STATIC_REWARD) for x in sizes), dtype=float)

def addFigText(optimal):
    plt.figtext(0.5, -0.03, f"Additional parameters: percentage reward={RELATIVE_REWARD*100}%, min days={MIN_PROB_DAYS}, ramp days={RAMP_UP}, max days={MAX_DAYS}", ha="center", fontsize=10)
    plt.figtext(0.5, -0.08, f"Optimal UTXO Size: {optimal:.6f} PPC", ha="center", fontsize=10)

def plotResults(results, yLabel, title):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(np.divide(sizes,1), results)
    ax.set_xlabel("UTXO Size")
    ax.set_ylabel(yLabel)
    ax.set_title(title)
    addFigText(sizes[results.argmax()])
    plt.xscale("log")
    plt.grid(which="both")
    plt.show()

def averageMints(outValue, diff):
    probs = generateDailyProbs(outValue, diff)
    probFail = probs[-1]
    weightedTime = (DAYS_WITH_NO_MINT*probs).sum()
    return (1-probFail)/weightedTime/outValue*365

#MINTERS=SUPPLY**2*averageMints(EXAMPLE_SIZE,DIFF)/(100*BLOCKYEAR)

mintsForSizes = np.fromiter((averageMints(x, DIFF) for x in sizes), dtype=float)

#fig, rewardAx = plt.subplots(figsize=(10, 6))
#rewardAx.set_title(f"Rewards and Mints for diff={DIFF} static={STATIC_REWARD}")
#rewardAx.set_xlabel("UTXO Size")

#colour = "#A10"
#rewardAx.plot(sizes, rewardForSizes, color=colour)
#rewardAx.tick_params(axis ='y', labelcolor=colour) 
#rewardAx.set_ylabel("% Reward / Yr", color=colour)

#mintsAx = rewardAx.twinx()
#colour = "#04A"
#mintsAx.plot(sizes, mintsForSizes, color=colour)
#mintsAx.tick_params(axis ='y', labelcolor=colour) 
#mintsAx.set_ylabel("Mints / Coin / Yr", color=colour)

#addFigText(sizes[rewardForSizes.argmax()])

blockLoss = (1 - mintsForSizes[rewardForSizes.argmax()] / mintsForSizes.max())*100
#plt.figtext(0.5, -0.13, f"Blocks lost at optimum: -{blockLoss:.2f}%", ha="center", fontsize=10)

#plt.xscale("log")
#rewardAx.grid(which="both")
#plt.show()

with open('90day_diff.csv', newline='') as csvfile:
    RealData = list(csv.reader(csvfile))

#optMints=mintsForSizes.max()
print(len(RealData))
IntegerArray=list(range(1,len(RealData)))
DataArray=[]
UTXOArray=[]
avgdiff=0
n=0
i=0
for row in RealData[1:]:
    utxo=float(row[1].strip(' "'))
    thisdiff=float(row[2].strip(' "'))
    optMints=averageMints(0.01, thisdiff)
    DataArray.append(utxo*averageMints(utxo, thisdiff)/optMints)
    UTXOArray.append(utxo)
    avgdiff+=thisdiff*i
    n+=i
    i+=1
avgdiff=avgdiff/n
print(avgdiff)
avgCoinMint=sum(DataArray)/len(DataArray)
MintingCoins=BLOCKYEAR/(averageMints(avgCoinMint, avgdiff))

fig, dataAx = plt.subplots(figsize=(10, 6))
dataAx.scatter(UTXOArray, DataArray,alpha=0.03, c="#000")
plt.xscale("log")
plt.yscale("log")
plt.text(300, 20, "avgCoinMint=%.3f ppc"%(avgCoinMint), fontsize = 22)
plt.text(300, 10, "MintingCoins=%.0f ppc"%(MintingCoins), fontsize = 22)
dataAx.set_ylabel("UTXO size/mint")
dataAx.set_xlabel("UTXO Size")
plt.show()
