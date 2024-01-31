import pandas as pd
from datetime import datetime,timedelta

# 顯示固定路線
route_name_list = ['紅68A','紅68A(延駛大莊里)','紅68B','紅68B(部分繞駛嘉興國中)','60覺民幹線','60覺民幹線區間車',
                   '橘12(白天延駛澄清湖)','橘11A','橘11B','橘11A區間車','224']

# 時刻表資料
df_sch = pd.read_csv('tdx.csv',index_col=0)
df_sch = df_sch.loc[df_sch['RouteName'].isin(route_name_list)]
df_sch = df_sch[['RouteID','RouteName','Direction','TripID','StopSequence','StopName']]
df_sch = df_sch.groupby(['RouteID','RouteName','Direction'])\
                .agg(MinStopSequence=('StopSequence','min'),MaxStopSequence=('StopSequence','max')).reset_index()
df_sch_a = df_sch[['RouteID','RouteName','Direction','MinStopSequence']].rename(columns={'MinStopSequence':'StopSequence'})
df_sch_b = df_sch[['RouteID','RouteName','Direction','MaxStopSequence']].rename(columns={'MaxStopSequence':'StopSequence'})
df_sch = pd.concat([df_sch_a,df_sch_b])

# 公車實際行駛資料
df = pd.read_csv('Schedule_1.csv')
df = df.loc[df['RouteName'].isin(route_name_list)]
# 只顯示符合第一站和第n站末站資料
df = pd.merge(df,df_sch,left_on=['RouteID','RouteName','Direction','StopSequence'],right_on=['RouteID','RouteName','Direction','StopSequence'],how='right')
df = df.sort_values(by=['ReportDate','RouteID','RouteName','Direction','TRIP_ID','StopSequence'])

# 排除一： 獲取歷史資料時，依GPSTime進行排序，同個班次、路線、站牌的車子前後兩筆資料回傳時間差距過大
df = df.groupby(['ReportDate','PlateNumb','OperatorID','RouteID','RouteName','SubRouteID',
                     'SubRouteName','StopID','StopName','StopSequence','Direction','TRIP_ID'])\
       .agg(GPSTime=('GPSTime','max')).reset_index()
# 計算各班次行駛時間（班次結束時間-起始時間）
df = df.groupby(['ReportDate','PlateNumb','OperatorID','RouteID','RouteName','SubRouteID',
                 'SubRouteName','Direction','TRIP_ID'])\
       .agg(Max_GPSTime=('GPSTime','max'),Min_GPSTime=('GPSTime','min')).reset_index()
df.loc[:,'TravelTime'] = df.apply(lambda x: (datetime.strptime(x['Max_GPSTime'], '%Y-%m-%d %H:%M:%S')
                                         - datetime.strptime(x['Min_GPSTime'],'%Y-%m-%d %H:%M:%S')).total_seconds() / 60,axis=1)
# 顯示排班時程（以發車時間為主）
df.loc[:,'Min_Schedule_Time'] = df.apply(lambda x: datetime.strptime(x['Min_GPSTime'], '%Y-%m-%d %H:%M:%S').strftime('%H:00:00'),axis=1)
df.loc[:,'Max_Schedule_Time'] = df.apply(lambda x: (datetime.strptime(x['Min_GPSTime'], '%Y-%m-%d %H:%M:%S')+timedelta(hours=1)).strftime('%H:00:00'), axis=1)
df.loc[:,'Schedule_Time'] = df.apply(lambda x: x['Min_Schedule_Time']+'-'+x['Max_Schedule_Time'],axis=1)
# 排除二： 刪除該班次只有一筆資料（行駛時間為0）
df = df.loc[df['TravelTime'] != 0]

# 排除三： 刪除行駛時間異常值
# compute quantiles
quantiles = df.groupby(['RouteID','RouteName','Direction'])['TravelTime'].quantile([0.1, 0.9]).unstack()
# compute interquartile range for each prod
iqr = quantiles.diff(axis=1).bfill(axis=1)
# compute fence bounds
fence_bounds = quantiles + iqr * [-1.5, 1.5]
# check if units are outside their respective tukey ranges
df['flag'] = df.merge(fence_bounds, left_on=['RouteID','RouteName','Direction'], right_index=True).eval('not (`0.1` < TravelTime < `0.9`)').astype(int)
df = df.loc[(df['flag']==0)]

# 計算各路線每日行駛時間（包含排班時程資訊）
df = df.groupby(['ReportDate','RouteID','RouteName','Direction','Schedule_Time'])\
                .agg(AvgTravelTime=('TravelTime','mean')).reset_index()
df.loc[:, 'AvgTravelTime'] = df.apply(lambda x: float("{:.1f}".format(x['AvgTravelTime'])), axis=1)
df = df.sort_values(by=['RouteID','ReportDate'])

# 新增假日or平日標籤
df.loc[:,'weekday'] = df.apply(lambda x:datetime.strptime(x['ReportDate'],'%Y-%m-%d').weekday()+1,axis=1)
df.loc[:,'weekday'] = df.apply(lambda x:datetime.strptime(x['ReportDate'],'%Y-%m-%d').weekday()+1,axis=1)
df.loc[:,'Week'] = df.apply(lambda x:'假日' if x['weekday'] == 6 or x['weekday'] == 7 else '平日',axis=1)

# 計算各路線假日or平日行駛時間
df_total = df.groupby(['RouteID','RouteName','Schedule_Time','Direction','Week'])\
                    .agg(AvgTravelTime=('AvgTravelTime','mean')).reset_index()
df_total.loc[:, 'AvgTravelTime'] = df_total.apply(lambda x: float("{:.1f}".format(x['AvgTravelTime'])), axis=1)
df_total = df_total.pivot(columns='Schedule_Time', values='AvgTravelTime',index=['RouteID','RouteName','Direction','Week'])
df_total = df_total.reset_index()

print(df_total)