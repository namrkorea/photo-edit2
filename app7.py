import streamlit as st
import streamlit.elements.image as st_image
from PIL import Image
import io
import numpy as np
from rembg import remove
import cv2
from streamlit_drawable_canvas import st_canvas
import base64

# ==========================================
# 🚨 [시스템 패치] 사라진 image_to_url 함수 복구
# 이 부분이 있어야 붓 도구가 정상 작동합니다.
# ==========================================
def fixed_image_to_url(image, width, clamp, channels, output_format, image_id, allow_emoji=False):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

if not hasattr(st_image, 'image_to_url'):
    st_image.image_to_url = fixed_image_to_url
# ==========================================

# 1. 앱 설정
st.set_page_config(page_title="AI 매직 포토", page_icon="✨")

st.title("✨ AI 매직 포토 에디터")
st.write("배경을 지우거나, 원하지 않는 물체를 삭제해보세요!")

# 시스템 상태 표시 (성공 시 초록색 박스)
if hasattr(st_image, 'image_to_url'):
    st.success("✅ 시스템 정상 가동 중 (모든 기능 사용 가능)")

# 탭 나누기
tab1, tab2 = st.tabs(["✂️ 배경 제거", "🪄 물체 지우기"])

# --- 탭 1: 배경 제거 기능 ---
with tab1:
    st.header("배경을 투명하게 만들기")
    bg_file = st.file_uploader("사진 업로드 (배경 제거용)", type=["png", "jpg", "jpeg"], key="bg")

    if bg_file:
        image = Image.open(bg_file)
        # 경고 메시지 해결을 위해 use_column_width 사용
        st.image(image, caption="원본 사진", use_column_width=True)

        if st.button("배경 제거 실행 (AI)"):
            with st.spinner("AI가 배경을 지우는 중입니다..."):
                try:
                    output = remove(image)
                    st.success("완료!")
                    st.image(output, caption="배경 제거 결과", use_column_width=True)

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
        image_to_erase = Image.open(erase_file).convert("RGB")
        
        # 캔버스 너비 설정
        canvas_width = 350
        w_percent = (canvas_width / float(image_to_erase.size[0]))
        h_size = int((float(image_to_erase.size[1]) * float(w_percent)))
        
        resized_image = image_to_erase.resize((canvas_width, h_size))

        stroke_width = st.slider("붓 크기 조절", 1, 50, 15)
        
        # 캔버스 그리기
        try:
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",
                stroke_width=stroke_width,
                stroke_color="#ff0000",
                background_image=resized_image,
                update_streamlit=True,
                height=h_size,
                width=canvas_width,
                drawing_mode="freedraw",
                key="canvas",
            )
        except AttributeError:
            st.error("⚠️ 페이지를 새로고침 해주세요.")
            st.stop()

        if st.button("선택한 영역 지우기"):
            if canvas_result.image_data is not None:
                with st.spinner("지우는 중..."):
                    try:
                        img_array = np.array(resized_image)
                        mask_data = canvas_result.image_data
                        mask = mask_data[:, :, 3].astype('uint8')
                        
                        inpainted_img = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)
                        
                        final_result = Image.fromarray(inpainted_img)
                        st.success("삭제 완료!")
                        st.image(final_result, caption="결과", use_column_width=True)

                        buf2 = io.BytesIO()
                        final_result.save(buf2, format="JPEG")
                        byte_im2 = buf2.getvalue()
                        st.download_button(
                            label="사진 다운로드",
                            data=byte_im2,
                            file_name="erased_photo.jpg",
                            mime="image/jpeg"
                        )
                    except Exception as e:
                        st.error(f"오류: {e}")
            else:
                st.warning("먼저 지우고 싶은 부분을 칠해주세요!")
