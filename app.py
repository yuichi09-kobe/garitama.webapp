import streamlit as st # type: ignore
import cv2
import tempfile
import math

from streamlit_image_coordinates import streamlit_image_coordinates # type: ignore

st.set_page_config(
    page_title="ガリタマ",
    layout="wide"
)

st.title("⚾ ティー打撃飛距離推定")

# ------------------------
# Session State
# ------------------------

for key in [
    "x1",
    "y1",
    "x2",
    "y2",
    "left_x",
    "right_x",
    "ball_px"
]:
    if key not in st.session_state:
        st.session_state[key] = None

# ------------------------
# 動画アップロード
# ------------------------

uploaded_file = st.file_uploader(
    "動画を選択",
    type=["mp4", "mov", "MOV", "MP4"]
)

if uploaded_file:

    st.success("動画アップロード成功")

    st.video(uploaded_file)

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    )

    temp_file.write(
        uploaded_file.read()
    )

    video_path = temp_file.name

    cap = cv2.VideoCapture(
        video_path
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    frame_count = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    st.write(
        f"FPS : {fps:.2f}"
    )

    st.write(
        f"総フレーム数 : {frame_count}"
    )

    # ------------------------
    # フレーム選択
    # ------------------------

    col1, col2 = st.columns(2)

    with col1:

        frame1 = st.slider(
            "開始フレーム",
            0,
            frame_count - 1,
            0
        )

    with col2:

        frame2 = st.slider(
            "終了フレーム",
            0,
            frame_count - 1,
            min(
                100,
                frame_count - 1
            )
        )

    # ------------------------
    # 開始フレーム取得
    # ------------------------

    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        frame1
    )

    ret1, img1 = cap.read()

    # ------------------------
    # 終了フレーム取得
    # ------------------------

    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        frame2
    )

    ret2, img2 = cap.read()

    # ------------------------
    # 表示
    # ------------------------

    col1, col2 = st.columns(2)

    if ret1:

        with col1:

            frame_rgb1 = cv2.cvtColor(
                img1,
                cv2.COLOR_BGR2RGB
            )

            st.image(
                frame_rgb1,
                caption=f"開始フレーム {frame1}",
                use_container_width=True
            )

            st.write(
                "① ボール中心をクリック"
            )

            center_point = streamlit_image_coordinates(
                frame_rgb1,
                key="center_point"
            )

            if center_point:

                st.session_state.x1 = center_point["x"]
                st.session_state.y1 = center_point["y"]

            st.write(
                "② ボール左端をクリック"
            )

            left_point = streamlit_image_coordinates(
                frame_rgb1,
                key="left_point"
            )

            if left_point:

                st.session_state.left_x = left_point["x"]

            st.write(
                "③ ボール右端をクリック"
            )

            right_point = streamlit_image_coordinates(
                frame_rgb1,
                key="right_point"
            )

            if right_point:

                st.session_state.right_x = right_point["x"]

            if (
                st.session_state.left_x is not None
                and
                st.session_state.right_x is not None
            ):

                st.session_state.ball_px = abs(
                    st.session_state.right_x
                    -
                    st.session_state.left_x
                )

            st.write(
                f"開始座標 : ({st.session_state.x1}, {st.session_state.y1})"
            )

            st.write(
                f"ボール直径 : {st.session_state.ball_px}"
            )

    if ret2:

        with col2:

            frame_rgb2 = cv2.cvtColor(
                img2,
                cv2.COLOR_BGR2RGB
            )

            st.image(
                frame_rgb2,
                caption=f"終了フレーム {frame2}",
                use_container_width=True
            )

            st.write(
                "④ 終了位置をクリック"
            )

            end_point = streamlit_image_coordinates(
                frame_rgb2,
                key="end_point"
            )

            if end_point:

                st.session_state.x2 = end_point["x"]
                st.session_state.y2 = end_point["y"]

            st.write(
                f"終了座標 : ({st.session_state.x2}, {st.session_state.y2})"
            )

    # ------------------------
    # 値取得
    # ------------------------

    x1 = st.session_state.x1
    y1 = st.session_state.y1

    x2 = st.session_state.x2
    y2 = st.session_state.y2

    ball_px = st.session_state.ball_px

    st.divider()

    if st.button("計算開始"):

        if (
            x1 is None
            or y1 is None
            or x2 is None
            or y2 is None
            or ball_px is None
        ):

            st.error(
                "全てのクリックを完了してください"
            )

        elif frame2 <= frame1:

            st.error(
                "終了フレームは開始フレームより後にしてください"
            )

        else:

            BALL_DIAMETER_MM = 72

            mm_per_px = (
                BALL_DIAMETER_MM /
                ball_px
            )

            dx = x2 - x1
            dy = y1 - y2

            angle = math.degrees(
                math.atan2(
                    dy,
                    dx
                )
            )

            distance_px = math.sqrt(
                dx ** 2
                +
                dy ** 2
            )

            distance_m = (
                distance_px
                *
                mm_per_px
            ) / 1000

            time_s = (
                frame2
                -
                frame1
            ) / fps

            speed_mps = (
                distance_m
                /
                time_s
            )

            speed_kmh = (
                speed_mps * 3.6
            )

            horizontal_speed = (
                speed_mps
                *
                math.cos(
                    math.radians(angle)
                )
            )

            vertical_speed = (
                speed_mps
                *
                math.sin(
                    math.radians(angle)
                )
            )

            flight_time = (
                vertical_speed
                +
                math.sqrt(
                    vertical_speed ** 2
                    +
                    2 * 9.8 * 1
                )
            ) / 9.8

            theoretical_distance = (
                flight_time
                *
                horizontal_speed
            )

            distance = (
                0.8215
                *
                theoretical_distance
                +
                2.5221
            )

            st.subheader(
                "解析結果"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "角度",
                    f"{angle:.2f}°"
                )

            with c2:

                st.metric(
                    "速度",
                   f"{speed_kmh:.2f} km/h"
                )

            with c3:

                st.metric(
                    "飛距離",
                    f"{distance:.2f} m"
                )

    cap.release()
