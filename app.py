import os
import json

import streamlit as st
from PIL import Image

import module

st.title("戦績入力アプリ")
st.write("---")
# プレイヤー名
names = ["isanacat", "Yugen", "LuckyNana", "pecoson", "amondo22", "Lily"]
# データフォルダが存在しない場合は作成
if not os.path.exists("img_data"):
    os.makedirs("img_data")

st.header("画像アップローダー")

# ファイルアップローダーを作成
uploaded_file = st.file_uploader("画像をドラッグ&ドロップしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像を表示
    image = Image.open(uploaded_file)
    st.image(image, caption='アップロードされた画像', use_column_width=True)
    
    # 画像を保存
    save_path = os.path.join("img_data", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"画像が正常に保存されました: {save_path}")
    if uploaded_file is not None:
        ocr = module.OCR(save_path)
    sheet_path = st.secrets["sheet_path"]
    spread_sheet = module.get_spreadsheet_connection(sheet_path)
    if 'characters' not in st.session_state:
        st.session_state['characters'], st.session_state['enemy_teams'], st.session_state['map_option'] = module.get_variable(spread_sheet)
    characters = st.session_state['characters']
    enemy_teams = st.session_state['enemy_teams']
    map_option = st.session_state['map_option']

    st.header("キャラクター選択")
    # 2列でキャラクター選択UIを表示
    col1, col2 = st.columns(2)
    selected_characters = []
    for i, name in enumerate(names):
        with col1 if i % 2 == 0 else col2:
            selected = st.selectbox(f"{name} のキャラクターを選んでください", characters, key=name)
            if selected != "None":
                selected_characters.append(selected)
    if len(selected_characters) > 5:
        st.error("6キャラクター選ばれています。")
    elif (len(set(selected_characters)) < 5 and selected_characters.count("None") < 2) and len(selected_characters) > 4:
        st.error("キャラクターがかぶっています")
    elif len(selected_characters) < 5:
        st.error("Noneが多すぎます")
    else:
        result_list = ocr.main()
        swap_list = module.swap_elements(result_list,names)
        df = module.df_create(swap_list)
        st.header("データに間違いがあれば修正してください")
        col1, col2 = st.columns([1, 1])
        with col1:
            edited_df = st.data_editor(df,
                                   num_rows="fixed",
                                   hide_index=True,)
        with col2:
            st.image(image, caption='アップロードされた画像', use_column_width=True)
        base_df,worksheet = module.get_base_df(spread_sheet)
        st.header("基礎情報の入力")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            insert_index_text = st.text_input("挿入する行を入力してください")
            if not insert_index_text.isdigit():
                st.error("自然数を入力してください")
            elif int(insert_index_text) < 1:
                st.error("1以上で入力してください")
            else:
                insert_index = int(insert_index_text)
                # 行の見え方が違うため1引く
                insert_index -= 1
        
            with col2:
                insert_patch = st.text_input("patchを入力してください")
        
            with col3:
                insert_oppo = st.selectbox("敵チームを選択してください", enemy_teams)
        
            insert_map = st.selectbox("mapを選択してください",map_option)
        
            if st.button("決定"):
                edited_df["character"] = selected_characters
                edited_df["acs"] = edited_df["acs"].astype(int)
                edited_df["kill"] = edited_df["kill"].astype(int)
                edited_df["death"] = edited_df["death"].astype(int)
                edited_df["assist"] = edited_df["assist"].astype(int)
                module.update(insert_index,insert_patch,insert_oppo,insert_map,base_df,edited_df,worksheet)
                st.success("正常に更新された気がする")
                st.balloons()
        
            if st.button("初めに戻る"):
                st.markdown(
            """
            <script>
                window.parent.location.reload();
            </script>
            """,
            unsafe_allow_html=True
        )
