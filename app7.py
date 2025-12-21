import streamlit as st
from PIL import Image
import io
import numpy as np
from rembg import remove
import cv2
from streamlit_drawable_canvas import st_canvas

# 1. 앱 설정
st.set_page_config(page_title="AI 매직 포토", page_icon="✨")

st.title("✨ AI 매직 포토 에디터")
st.write("배경을 지우거나, 원하지 않는 물체를 삭제해보세요!")

# 탭 나누기 (기능별로 화면 분리)
tab1, tab2 = st.tabs(["✂️ 배경 제거", "🪄 물체 지우기"])

# --- 탭 1: 배경 제거 기능 ---
with tab1:
    st.header("배경을 투명하게 만들기")
    bg_file = st.file_uploader("사진 업로드 (배경 제거용)", type=["png", "jpg", "jpeg"], key="bg")

    if bg_file:
        image = Image.open(bg_file)
        st.image(image, caption="원본 사진", use_column_width=True)

        # 버튼을 누르면 AI 작동
        if st.button("배경 제거 실행 (AI)"):
            with st.spinner("AI가 배경을 지우는 중입니다..."):
                try:
                    # rembg 라이브러리로 배경 제거
                    output = remove(image)
                    st.success("완료!")
                    st.image(output, caption="배경 제거 결과", use_column_width=True)

                    # 다운로드 버튼
                    buf = io.BytesIO()
                    output.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    st.download_button(
                        label="투명 배경 사진 다운로드",
                        data=byte_im,
                        file_name="no_bg.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

# --- 탭 2: 물체 지우기 (매직 이레이저) ---
with tab2:
    st.header("원하지 않는 부분 지우기")
    st.info("지우고 싶은 부분을 붓으로 색칠하고 '지우기' 버튼을 누르세요.")
    
    erase_file = st.file_uploader("사진 업로드 (지우기용)", type=["png", "jpg", "jpeg"], key="erase")

    if erase_file:
        # 캔버스 설정을 위한 이미지 로드
        image_to_erase = Image.open(erase_file).convert("RGB")
        
        # 캔버스 크기 조정 (모바일 화면 고려)
        # 이미지의 가로세로 비율 유지하며 리사이징
        canvas_width = 350 # 모바일에서 적당한 크기
        w_percent = (canvas_width / float(image_to_erase.size[0]))
        h_size = int((float(image_to_erase.size[1]) * float(w_percent)))
        resized_image = image_to_erase.resize((canvas_width, h_size))

        # 그리기 도구 설정 (스트로크 두께, 색상 등)
        stroke_width = st.slider("붓 크기 조절", 1, 50, 15)
        
        # 캔버스 띄우기 (여기에 그림을 그림)
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # 채우기 색 (투명도)
            stroke_width=stroke_width,
            stroke_color="#ff0000", # 붓 색상 (빨강)
            background_image=resized_image,
            update_streamlit=True,
            height=h_size,
            width=canvas_width,
            drawing_mode="freedraw",
            key="canvas",
        )

        if st.button("선택한 영역 지우기"):
            if canvas_result.image_data is not None:
                with st.spinner("마법을 부리는 중..."):
                    # 1. 원본 이미지를 numpy 배열로 변환
                    img_array = np.array(resized_image)
                    
                    # 2. 사용자가 그린 부분(마스크) 추출
                    mask_data = canvas_result.image_data
                    mask = mask_data[:, :, 3] # 알파 채널만 가져옴 (그린 부분)
                    
                    # 3. OpenCV의 Inpainting 기술 적용 (주변 색으로 채우기)
                    # Telea 알고리즘 사용
                    inpainted_img = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)
                    
                    # 4. 결과 보여주기
                    final_result = Image.fromarray(inpainted_img)
                    st.image(final_result, caption="지우기 완료!", use_column_width=True)

                    # 다운로드
                    buf2 = io.BytesIO()
                    final_result.save(buf2, format="JPEG")
                    byte_im2 = buf2.getvalue()
                    st.download_button(
                        label="수정된 사진 다운로드",
                        data=byte_im2,
                        file_name="erased_photo.jpg",
                        mime="image/jpeg"
                    )