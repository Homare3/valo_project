import os
import json

import streamlit as st
from PIL import Image

import module


# プレイヤー名
names = ["isanacat", "Yugen", "LuckyNana", "pecoson", "amondo22", "Lily"]


# データフォルダが存在しない場合は作成
if not os.path.exists("img_data"):
    os.makedirs("img_data")

st.title("画像アップローダー")

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
    ocr = module.OCR(save_path)
    sheet_path = st.secrets["sheet_path"]
    characters,enemy_teams,map_option,spread_sheet = module.get_variable(sheet_path)

    st.title("キャラクター選択")
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
        fix_list = module.name_fix(result_list,names)
        swap_list = module.swap_elements(result_list,names)
        base_data = module.split_list(swap_list)
        df = module.df_create(base_data)
        
        base_df,worksheet = module.connected_spread_sheet(spread_sheet)

        st.title("基礎情報の入力")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # insert_index = st.number_input("挿入する行を入力してください",min_value=0,step=10)
            insert_index = int(st.text_input("挿入する行を入力してください"))
            # 行の見え方が違うため1引く
            insert_index -= 1
        
        with col2:
            insert_patch = st.text_input("patchを入力してください")
        
        with col3:
            insert_oppo = st.selectbox("敵チームを選択してください", enemy_teams)
        
        insert_map = st.selectbox("mapを選択してください",map_option)
        
        if st.button("決定"):
            df["character"] = selected_characters
            df["avc"] = df["avc"].astype(int)
            df["kill"] = df["kill"].astype(int)
            df["death"] = df["death"].astype(int)
            df["assist"] = df["assist"].astype(int)
            module.update(insert_index,insert_patch,insert_oppo,insert_map,base_df,df,worksheet)
            st.success("正常に更新された気がする")
        
        if st.button("初めに戻る"):
            st.markdown(
        """
        <script>
            window.parent.location.reload();
        </script>
        """,
        unsafe_allow_html=True
    )