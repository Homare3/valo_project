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


class OCR:
    def __init__(self,path):
        # self.credentials = service_account.Credentials.from_service_account_file('./data/key.json')
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
            result_list = self.get_word(text_xpos_list)
            # st.write(text_annotations)
            # sorted_annotations = self.sort_annotations(text_annotations[1:])
            # result_list = [annotation.description for annotation in sorted_annotations]
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
                    [text_xpos_list.append([symbol.text, symbol.bounding_box.vertices[0].x]) for symbol in word.symbols if symbol.text != "/"]
        return text_xpos_list
    
    def get_word(self,text_xpos_list):
        word_list = []
        save_xpos = 0
        for text,xpos in text_xpos_list:
            if -20 <= (xpos - save_xpos) <= 20:
                word_list[-1] += text
            else:
                word_list.append(text)
            save_xpos = xpos
        
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
        

def name_fix(result_list,names):
  for i in range(len(result_list)):
    if not result_list[i].isdigit() and result_list[i] != "/":
      # namesに一部一致しているか確認
      for name in names:
        if result_list[i] in name:
          result_list[i] = name
  for j in names:
    index = [i for i, x in enumerate(result_list) if x == j]
    if len(index) > 1:
      result_list.pop(index[1])
  return result_list


# 順番を入れ替える関数
def swap_elements(result_list,names):
  new_list = []
  for name in names:
    for index, item in enumerate(result_list):
     if item == name and item not in new_list:
        for i,group in enumerate(result_list[index:]):
          if group in names and i != 0:
            break
          else:
            new_list.append(group)

  return new_list


# /と空白があれば別々の要素とする
def split_list(result_list):
  new_list = []
  for item in result_list:
    if "/" in item:
      new_list.extend(item.split("/"))
    elif " " in item:
      new_list.extend(item.split(" "))
    else:
      new_list.append(item)
  # ""だけ除去
  new_list = [item for item in new_list if item != ""]
  return new_list


# dataframeにする
def df_create(result_list):
  df = pd.DataFrame(columns=["name","avc","kill","death","assist"])
  # 5つずつ
  for i in range(0,len(result_list),5):
    df.loc[len(df)] = result_list[i:i+5]
  return df


# 選択肢を取得
@st.cache_data
def get_variable(path):
  scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]
  #  credentials = Credentials.from_service_account_file(
  #   './data/key.json',
  #   scopes=scopes
  #   )
  credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
  gc = gspread.authorize(credentials)
  spread_sheet = gc.open_by_url(path)
  work_sheet = spread_sheet.worksheet("R63")
  values = work_sheet.get_all_values(value_render_option='FORMULA')
  var_df = pd.DataFrame(data=values[1:],columns=values[0])
  characters = ["None"] + list(var_df[var_df["エージェント"]!=""]["エージェント"])
  enemy_team = list(var_df[var_df["略称"]!=""]["略称"])
  insert_map = list(var_df[var_df["マップ"]!=""]["マップ"])
  return characters,enemy_team,insert_map,spread_sheet


# shread sheetと接続
def connected_spread_sheet(spread_sheet):
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
def update(insert_index,insert_patch,insert_oppo,insert_map,base_df,df,worksheet):
    index_dict = {"isanacat":[8,5,6,7,9],
                  "Yugen":[14,11,12,13,15],
                  "LuckyNana":[20,17,18,19,21],
                  "pecoson":[26,23,24,25,27],
                  "amondo22":[32,29,30,31,33],
                  "Lily":[38,35,36,37,39]
                  }
    
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
