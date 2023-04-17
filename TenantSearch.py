import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import zipfile
from PIL import Image

dbname='RTS.db'
conn=sqlite3.connect(dbname)
cur=conn.cursor()
sql=f"""
    SELECT * 
        FROM Version
"""
df_Key=pd.read_sql_query(sql,conn)
conn.commit()
conn.close()





st.set_page_config(layout="wide")
st.title('Retail Tenant Search APP')
with st.sidebar:
    zip_RTS=st.file_uploader(label='Upload RTS.zip',type='zip')
    
    
    
if zip_RTS is None:
    image=Image.open('ACube.PNG')
    st.image(image,width=400)
    

if zip_RTS is not None:
    Version_RTS=zip_RTS.name.replace('.zip','')
    Key_RTS=df_Key[df_Key.Version==Version_RTS].Key.values[0]
    zf=zipfile.ZipFile(zip_RTS,'r')
    zf.setpassword(bytes(Key_RTS,'utf-8'))
    with zf as z:
        with z.open('PropertyTenant.csv') as f:
            df_PT=pd.read_csv(f,encoding='utf-8',dtype=str)
        with z.open('Tenant.csv') as f:
            df_Tenant=pd.read_csv(f,encoding='utf-8',dtype=str)
        
    df_PT.Tsubo=df_PT.Tsubo.astype(float)
    df_PT_Main=df_PT.copy()
    
    Mcol1,Mcol2=st.columns(2)
    with Mcol1:
        AreaInList=st.multiselect(
            label='In Area | 出店しているエリア',
            options=['銀座','新宿','原宿','表参道','渋谷','京都','神戸','心斎橋','栄','天神'],
            default=['銀座']
        )
        AreaNotList=st.multiselect(
            label='Not in Area | 出店していないエリア',
            options=['銀座','新宿','原宿','表参道','渋谷','京都','神戸','心斎橋','栄','天神'],
            default=[]
        )
        
        ColorList=st.multiselect(
            label='Area Color | エリア 色',
            options=['赤','黄','青','白'],
            default=[]
        )
        BusinessList=st.multiselect(
            label='Business | 業態',
            options=[
                '食物販・飲食店', 'アパレル', 'その他 物販', 'ラグジュアリー', '靴・カバン', 'ジュエリー・アクセサリー',
                'その他 施設', 'アウトドア・スポーツ', 'リユース', '時計・メガネ', 'ドラッグストア', 'ヘルス&ビューティー', '金融',
                'コンビニ', 'SC・百貨店', '家具・雑貨', 'エンターテイメント', 'デジタル・通信', 'ファッション小物', 'ショールーム',
                '大型量販店', 'ブライダル', 'アンテナショップ',  '医療', 'ファッション'
            ],
            default=[]
        )
        start_Size,end_Size=st.select_slider(
            label='Size (Tsubo) | 賃貸面積 (坪) ',
            options=[0,25,50,75,100,150,200,250,300,350,400,450,500,1000,2500,5000,10000],
            value=(0,10000)
        )
        start_BA,end_BA=st.select_slider(
            label='Building Age | 築年数 ',
            options=['新築','1～3年未満','3～5年未満','5～10年未満','10～20年未満','20～30年未満','30～40年未満','40～50年未満','50年以上'],
            value=('新築','50年以上')
        )
        BARangeList=['新築','1～3年未満','3～5年未満','5～10年未満','10～20年未満','20～30年未満','30～40年未満','40～50年未満','50年以上']
        BARangeList=BARangeList[BARangeList.index(start_BA):BARangeList.index(end_BA)+1]
        MultiFloorBool=st.radio(
            label='Multi-Floor Shop | 複数階店舗',
            options=['指定なし','有り','無し'],
            horizontal=True,
        )
    
    AreaCol=['Tenant']
    if len(AreaInList)!=0:
        for Area in AreaInList:
            AreaCol.append(f'In{Area}')
    if len(AreaNotList)!=0:
        for Area in AreaNotList:
            AreaCol.append(f'NotIn{Area}')
    df_Tenant=df_Tenant[AreaCol]    
    df_PT=df_PT[df_PT.Area.isin(AreaInList)].reset_index(drop=True)
    
    
    if len(ColorList)!=0:
        df_PT=df_PT[df_PT.BM_Color.isin(ColorList)].reset_index(drop=True)
        df_Tenant=pd.merge(
            df_Tenant,
            df_PT[['Tenant']].drop_duplicates().assign(Color='●'),
            how='outer'
        )
    if len(BusinessList)!=0:
        df_PT=df_PT[df_PT.Business.isin(BusinessList)].reset_index(drop=True)
        df_Tenant=pd.merge(
            df_Tenant,
            df_PT[['Tenant']].drop_duplicates().assign(Business='●'),
            how='outer'
        )
    df_PT=df_PT[
        (df_PT.Tsubo>start_Size)&
        (df_PT.Tsubo<=end_Size)
    ].reset_index(drop=True)
    df_Tenant=pd.merge(
        df_Tenant,
        df_PT[['Tenant']].drop_duplicates().assign(Size='●'),
        how='outer'
    )
    df_PT=df_PT[df_PT.BldgAgeRange.isin(BARangeList)].reset_index(drop=True)
    df_Tenant=pd.merge(
        df_Tenant,
        df_PT[['Tenant']].drop_duplicates().assign(BuildingAge='●'),
        how='outer'
    )
    if MultiFloorBool=='有り':
        df_PT=df_PT[(df_PT.NumFloor.notnull())&(df_PT.NumFloor!='1')].reset_index(drop=True)
        df_Tenant=pd.merge(
            df_Tenant,
            df_PT[['Tenant']].drop_duplicates().assign(Floor='●'),
            how='outer'
        )
    if MultiFloorBool=='無し':
        df_PT=df_PT[(df_PT.NumFloor.notnull())&(df_PT.NumFloor=='1')].reset_index(drop=True)
        df_Tenant=pd.merge(
            df_Tenant,
            df_PT[['Tenant']].drop_duplicates().assign(Floor='●'),
            how='outer'
        )
    df_Tenant=df_Tenant.assign(
        Point=(df_Tenant=='●'
    ).sum(axis=1)).sort_values(['Point','Tenant'],ascending=False).reset_index(drop=True)
    ColList=df_Tenant.columns.tolist()
    NewColList=ColList[0:1]+ColList[-1:]+ColList[1:-1]
    df_Tenant=df_Tenant[NewColList]
    
    df_Tenant=df_Tenant.assign(View=False)[['View']+df_Tenant.columns[:-1].tolist()]
        
    with Mcol2:
        with st.expander(label='Tenant List',expanded=True):
            df_Tenant=st.experimental_data_editor(df_Tenant,height=500,use_container_width=True)
        
    
    
    with st.expander(label='Property Tenant Data',expanded=True):
        
        if len(df_Tenant[df_Tenant.View==True])!=0:
            AllArea=st.checkbox('選択されたテナントの全データを閲覧する')
            if AllArea:
                df_PT_Display=df_PT_Main[
                    df_PT_Main.Tenant.isin(df_Tenant[df_Tenant.View==True].Tenant)
                ].sort_values('Tenant',ascending=False).reset_index(drop=True)
            else:
                df_PT_Display=df_PT[
                    df_PT.Tenant.isin(df_Tenant[df_Tenant.View==True].Tenant)
                ].sort_values('Tenant',ascending=False).reset_index(drop=True)
        else:
            df_PT_Display=df_PT[
                df_PT.Tenant.isin(df_Tenant.dropna().Tenant)
            ].sort_values('Tenant',ascending=False).reset_index(drop=True)    
        st.dataframe(df_PT_Display,height=500,use_container_width=True)
        
    with st.sidebar:
        st.metric('Number of Tenants',len(df_Tenant.dropna()))