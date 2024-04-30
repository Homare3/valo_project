import cv2
import mediapipe as mp
import socket 
import time
from Socket import Socket 


client = Socket() 

# landmarkの繋がり表示用
landmark_line_ids = [ 
    (0, 1), (1, 5), (5, 9), (9, 13), (13, 17), (17, 0),  # 掌
    (1, 2), (2, 3), (3, 4),         # 親指
    (5, 6), (6, 7), (7, 8),         # 人差し指
    (9, 10), (10, 11), (11, 12),    # 中指
    (13, 14), (14, 15), (15, 16),   # 薬指
    (17, 18), (18, 19), (19, 20),   # 小指
]

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,                # 最大検出数
    min_detection_confidence=0.7,   # 検出信頼度
    min_tracking_confidence=0.7     # 追跡信頼度
)


n = 0
lm_pos1 = 0.0
test = [0,0]
test2 = [0,0]
count = 0
keep = [0,0]
tes = []
tes2 = []
cou = 0
check = 0
tesly = ""

rtest = [0,600]
ltest = [0,0]

specil = [0,0]
cap = cv2.VideoCapture(0)   # カメラのID指定
input(print(cap.isOpened()))
if cap.isOpened():
    input()
    while True:
        
        count = 0
        # カメラから画像取得
        success, img = cap.read()
        if not success:
            continue
        img = cv2.flip(img, 1)          # 画像を左右反転
        img_h, img_w, _ = img.shape     # サイズ取得

        # 検出処理の実行
        results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        startpoint = (0, 220)
        endpoint = (640, 220)
        go_startpoint = (213, 220)
        go_endpoint = (213, 720)
        back_startpoint = (426, 220)
        back_endpoint = (426, 720)

        linecolor = (0, 255, 0)
        linethick = 2

        cv2.line(img, startpoint, endpoint, linecolor, linethick)
        cv2.line(img, go_startpoint, go_endpoint, linecolor, linethick)
        cv2.line(img, back_startpoint, back_endpoint, linecolor, linethick)
        cv2.putText(img, "go", (430, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "stop", (230, 245), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "back", (10, 245), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "jump", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        
        if results.multi_hand_landmarks:
            # 検出した手の数分繰り返し
            for h_id, hand_landmarks in enumerate(results.multi_hand_landmarks):

                # landmarkの繋がりをlineで表示
                for line_id in landmark_line_ids:
                    # 1点目座標取得
                   
                    count += 1
                    lm = hand_landmarks.landmark[line_id[0]]
                    lm_pos1 = (int(lm.x * img_w), int(lm.y * img_h))
                  
                    # 2点目座標取得
                    
                    lm = hand_landmarks.landmark[line_id[1]]
                    lm_pos2 = (int(lm.x * img_w), int(lm.y * img_h))
                    # line描画
                    cv2.line(img, lm_pos1, lm_pos2, (128, 0, 0), 1)
                    if count == 12:
                        test = list(lm_pos2)
                    elif count == 15:
                        test2 = list(lm_pos2)
                    
                    
      
                
                # landmarkをcircleで表示
                z_list = [lm.z for lm in hand_landmarks.landmark]
                z_min = min(z_list)
                z_max = max(z_list)
                for lm in hand_landmarks.landmark:
                    lm_pos = (int(lm.x * img_w), int(lm.y * img_h))
                    lm_z = int((lm.z - z_min) / (z_max - z_min) * 255)
                    cv2.circle(img, lm_pos, 3, (255, lm_z, lm_z), -1)

                # 検出情報をテキスト出力
                # - テキスト情報を作成
                hand_texts = []
                for c_id, hand_class in enumerate(results.multi_handedness[h_id].classification):
                    if hand_class.label == "Right":
                        rtest = test
                    else:
                        ltest = test
                    hand_texts.append("#%d-%d" % (h_id, c_id)) 
                    hand_texts.append("- Index:%d" % (hand_class.index))
                    hand_texts.append("- Label:%s" % (hand_class.label))
                    hand_texts.append("- Score:%3.2f" % (hand_class.score * 100))
                    tesly = h_id
                    
                # - テキスト表示に必要な座標など準備
                lm = hand_landmarks.landmark[0]
                lm_x = int(lm.x * img_w) - 50
                lm_y = int(lm.y * img_h) - 10
                lm_c = (64, 0, 0)
                font = cv2.FONT_HERSHEY_SIMPLEX
                # - テキスト出力
                for cnt, text in enumerate(hand_texts):
                    cv2.putText(img, text, (lm_x, lm_y + 10 * cnt), font, 0.3, lm_c, 1)

        # 画像の表示
        cv2.drawMarker(img,
               position=rtest,
               color=(0, 255, 0),
               markerType=cv2.MARKER_CROSS,
               markerSize=20,
               thickness=2,
               line_type=cv2.LINE_4
               )
        cv2.imshow("MediaPipe Hands", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q') or key == 0x1b:
            break

        
        
        check = 0
        tes.append(test[1])
        tes2.append(test2[1])
        cou += 1
        if cou == 3:
            for i,j in zip(tes,tes2):
                if i > j:
                    check += 1

            cou = 0
            tes = []
            tes2 = []
       
        move_send = 0
        jump_send = 0
        dash_send = 0
        reset_send = 0


#ソケット通信
       
       # if check > 1:
        #    move_send = 2
        if ltest[0] != 0:
            reset_send = 1
        
       

        if rtest[0] > 0 and rtest[0] <= 213:
            
            move_send = -1
        elif rtest[0] > 213 and rtest[0] <= 390:
            move_send = 0

        elif 390 < rtest[0]:
            move_send = 1
        else:
            move_send = 0
        if rtest[1] < 220:
            jump_send = 1
       

        client.sendto([move_send,jump_send,reset_send])
        test = [0,0]
        test2 = [0,0]
        keep = [0,0]
        ltest = [0,0]
        rtest = [0,600]
cap.release()