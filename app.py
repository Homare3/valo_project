import os
import json

import streamlit as st
from PIL import Image

import module


characters = [
    "None","Astra", "Breach", "ぶりむstone", "Chamber", "Cypher", "Fade", "Gekko", 
    "Harbor", "Jett", "KAY/O", "Killjoy", "Neon", "Omen", "Phoenix", "Raze", 
    "Reyna", "Skye", "Sage", "Sova", "Viper", "Yoru", "ISO", "Deadlock", 
    "Clove", "Vyse"
]

names = ["isanacat", "Yugen", "LuckyNana", "pecoson", "amondo22", "Lily"]

# データフォルダが存在しない場合は作成
if not os.path.exists("data"):
    os.makedirs("data")

st.title("画像アップローダー")

# ファイルアップローダーを作成
uploaded_file = st.file_uploader("画像をドラッグ&ドロップしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像を表示
    image = Image.open(uploaded_file)
    st.image(image, caption='アップロードされた画像', use_column_width=True)
    
    # 画像を保存
    save_path = os.path.join("data", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"画像が正常に保存されました: {save_path}")
    ocr = module.OCR(save_path)

    st.title("キャラクター選択")
    # 各ユーザーごとにキャラクターを選択するUIを表示
    selected_characters = []
    for name in names:
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

        with open("./data/key_path.json","r",encoding="utf-8") as file:
            data = json.load(file)
        
        sheet_path = data.get("sheet_path")
        base_df,worksheet = module.connected_spread_sheet(sheet_path)

        st.title("基礎情報の入力")
        insert_index = st.number_input("挿入する行を入力してください",min_value=0,step=1)
        # 行の見え方が違うため1引く
        insert_index -= 1
        insert_patch = st.text_input("patchを入力してください")
        enemy_teams = data.get("enemy_team")
        insert_oppo = st.selectbox("敵チームを選択してください", enemy_teams)
        map_option = ["Haven", "Split", "Lotus", "Bind", "Ascent", "Sunset", "Breeze", "Icebox", "Abyss"]
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
            

    