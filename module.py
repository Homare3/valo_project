import os

import pandas as pd
import numpy as np
from datetime import datetime

from google.cloud import vision
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
import gspread

import streamlit as st

from oauth2client.service_account import ServiceAccountCredentials
import pytz
from google.cloud import storage

@st.cache_resource
class OCR:
    def __init__(self,path):
        self.credentials = service_account.Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), 
                                                                                 scopes = ["https://www.googleapis.com/auth/cloud-platform"],
                                                                                 )
        self.img_path = path
        self.client = vision.ImageAnnotatorClient(credentials=self.credentials)
    
    def main(self):
        with open(self.img_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = self.client.document_text_detection(image=image,
                                          image_context={"language_hints": ["ja", "en"]})
        if response.text_annotations:
            full_text_annotation = response.full_text_annotation
            text_xpos_list = self.get_text_and_xpos(full_text_annotation)
            y_ratio_group = self.row_group(text_xpos_list)
            result_list = self.get_word(y_ratio_group)
        else:
            print("No text detected")
        if response.error.message:
            raise Exception(
        '{}\nFor more info on error messages, check: '
        'https://cloud.google.com/apis/design/errors'.format(
            response.error.message))
        return result_list

    def get_text_and_xpos(self,full_text_annotation):
        text_xpos_list = []
        for blocks in full_text_annotation.pages[0].blocks:
            for paragraph in blocks.paragraphs:
                for word in paragraph.words:
                    [text_xpos_list.append([symbol.text, symbol.bounding_box.vertices[0].x, symbol.bounding_box.vertices[0].y]) for symbol in word.symbols if symbol.text != "/"]
        return text_xpos_list
    
    def has_exsist_row(self,y_ratio_groups,ypos):
       save_key = 999
       y_ratio_keys = list(y_ratio_groups.keys())
       for key in y_ratio_keys:
          if abs(key - ypos) < 6:
             save_key = key
       return save_key
        
    def row_group(self,text_xpos_list):
        y_ratio_groups = {}
        for text,xpos,ypos in text_xpos_list:
           save_key = self.has_exsist_row(y_ratio_groups,ypos)
           if save_key != 999:
              y_ratio_groups[save_key] += [[text,xpos]]
           else:
              y_ratio_groups[ypos] = [[text,xpos]]
        for key in y_ratio_groups:
           y_ratio_groups[key].sort(key=lambda x: x[1])
        return y_ratio_groups
    
    def get_word(self,y_ratio_group):
        word_list = []
        all_values = [item for sublist in y_ratio_group.values() for item in sublist]
        pixel_length = abs([item[1] for item in all_values if item[0] == "L" or item[0] == "p"][0] - max(all_values , key = lambda x: x[1])[1])        
        save_xpos = 0   
        for row_group in y_ratio_group.values():
           row_list = []
           for idx,(text,xpos) in enumerate(row_group,start=1):
              x_ratio = abs(xpos - save_xpos) / pixel_length
              if 0.03 < x_ratio <=  0.045:
                 continue
              elif 0.045 < x_ratio or idx == 1:
                 row_list += [text]
              else:
                 row_list[-1] += text
              save_xpos = xpos
           word_list.append(row_list)
        return word_list

    def get_center(self,annotation):
        vertices = annotation.bounding_poly.vertices
        center_x = sum(vertex.x for vertex in vertices) / len(vertices)
        center_y = sum(vertex.y for vertex in vertices) / len(vertices)
        return center_x, center_y
    
    def sort_annotations(self,annotations):
        # 中心のY座標でグループ化
        y_sorted = sorted(annotations, key=lambda a: self.get_center(a)[1])
        groups = []
        current_group = []
        last_y = None
        for annotation in y_sorted:
            current_y = self.get_center(annotation)[1]
            if last_y is None or abs(current_y - last_y) < 20:  # 20はグループ化の閾値
                current_group.append(annotation)
            else:
                groups.append(current_group)
                current_group = [annotation]
            last_y = current_y
        if current_group:
            groups.append(current_group)
        # 各グループ内でX座標でソート
        sorted_groups = [sorted(group, key=lambda a: self.get_center(a)[0]) for group in groups]
        # グループを平坦化
        return [annotation for group in sorted_groups for annotation in group]


# 順番を入れ替える関数
def swap_elements(result_list,names):
  def custom_sort(word):
     if word[0] in names:
        return names.index(word[0])
     return float("inf")
  new_list = [item for item in sorted(result_list, key=custom_sort) if item[0] in names]
  return new_list

# dataframeにする
def df_create(result_list):
  base_data = result_list.copy()
  df_data = []
  for word in result_list:

     if len(word) == 5:
        df_data += word
        continue
     elif len(word) < 5:
        df_data += [word + [None] * (5 - len(word))][0]
     else:
        df_data += word[:5]
  df = pd.DataFrame(columns=["name","acs","kill","death","assist"])
  # 5つずつ
  for i in range(0,len(df_data),5):
    df.loc[len(df)] = df_data[i:i+5]
  return df


# shread sheetと接続
@st.cache_resource
def get_spreadsheet_connection(path):
    scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(credentials)
    return gc.open_by_url(path)
   

# 選択肢を取得
def get_variable(spread_sheet):
  work_sheet = spread_sheet.worksheet("R63")
  values = work_sheet.get_all_values(value_render_option='FORMULA')
  var_df = pd.DataFrame(data=values[1:],columns=values[0])
  characters = ["None"] + list(var_df[var_df["エージェント"]!=""]["エージェント"])
  enemy_team = list(var_df[var_df["略称"]!=""]["略称"])
  insert_map = list(var_df[var_df["マップ"]!=""]["マップ"])
  return characters,enemy_team,insert_map

def get_players_name(spread_sheet):
   work_sheet = spread_sheet.worksheet("R63")
   values = work_sheet.get_all_values(value_render_option='FORMULA')
   var_df = pd.DataFrame(data=values[1:],columns=values[0])
   players_name = list(var_df[var_df["プレイヤー名"]!=""]["プレイヤー名"])
   
   return players_name

def get_base_df(spread_sheet):
    try:
        work_sheet = spread_sheet.worksheet("俺らの格差")
        values = work_sheet.get_all_values(value_render_option='FORMULA')
        base_df = pd.DataFrame(values)
        return base_df, work_sheet
    except gspread.exceptions.APIError as e:
        print(f"API Error: {e}")
        print(f"Response content: {e.response.content}")
        raise
    except GoogleAuthError as e:
        print(f"Authentication Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


# spread_sheetの更新
def update(insert_index,insert_patch,insert_oppo,insert_map,base_df,df,worksheet,names):
    index = [[8,5,6,7,9],[14,11,12,13,15],[20,17,18,19,21],[26,23,24,25,27],[32,29,30,31,33],[38,35,36,37,39]]
    index_dict = dict(zip(names,index))
    insert_date = datetime.now().strftime("%Y/%m/%d")
    insert_list = [insert_date,insert_patch,insert_oppo,insert_map]
 
    for i,item in enumerate(insert_list):
      base_df.iloc[insert_index,i] = item
    # dfのnameがkeyに一致する場合valueのリストの列にdfの値をそれぞれ入れる
    for name in df.name:
      for key,value in index_dict.items():
        if name == key:
          for items in df[df.name == name].drop(["name"],axis=1).values:
            for index,item in enumerate(items):
              base_df.iloc[insert_index,value[index]] = item
    worksheet.update('A1', base_df.values.tolist(),value_input_option='USER_ENTERED')
