import os
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer


# ---------- UTILS ----------
def download_images(url, folder="images", chapter=None):
    if not os.path.exists(folder):
        os.makedirs(folder)
    if chapter:
        folder = os.path.join(folder, f"chapter_{chapter}")
        os.makedirs(folder, exist_ok=True)

    response = requests.get(url)
    if response.status_code != 200:
        st.error(f"Failed to retrieve page: {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")
    image_paths = []

    for index, img in enumerate(img_tags, start=1):
        img_url = img.get("src")
        if not img_url:
            continue
        img_url = urljoin(url, img_url)

        try:
            img_data = requests.get(img_url).content
            file_extension = img_url.split(".")[-1].split("?")[0]
            file_path = os.path.join(folder, f"image_{index}.{file_extension}")
            with open(file_path, "wb") as f:
                f.write(img_data)
            image_paths.append(file_path)
        except Exception as e:
            st.warning(f"Failed to download {img_url}: {e}")

    return image_paths


def images_to_pdf(image_paths_dict, output_pdf):
    image_list = []
    for chapter in sorted(image_paths_dict):
        for img_path in image_paths_dict[chapter]:
            try:
                img = Image.open(img_path).convert("RGB")
                image_list.append(img)
            except Exception as e:
                st.warning(f"Skipping {img_path}: {e}")

    if image_list:
        image_list[0].save(output_pdf, save_all=True, append_images=image_list[1:])
        return output_pdf
    return None


def cleanup(image_paths_dict):
    for paths in image_paths_dict.values():
        for path in paths:
            try:
                os.remove(path)
            except:
                pass


# ---------- STREAMLIT MULTIPAGE ----------
st.set_page_config(page_title="Manga Gari", layout="centered")
pages = ["🖼️ Single Chapter", "📚 Multi-Chapter", "❓ How to Use"]
choice = st.sidebar.radio("Navigate", pages)

# ---------- PAGE 1 ----------
if choice == "🖼️ Single Chapter":
    st.title("📄 Manga Gari - Single Chapter to PDF")
    url = st.text_input("🔗 Enter the Chapter URL")
    pdf_name = st.text_input("📘 Output PDF name", "chapter")

    if st.button("Download Chapter"):
        if url and pdf_name:
            with st.spinner("Downloading images..."):
                image_paths = download_images(url)
                image_paths_dict = {1: image_paths}
                output_pdf = f"{pdf_name}.pdf"
                result = images_to_pdf(image_paths_dict, output_pdf)

                if result:
                    st.success("✅ PDF created!")
                    with open(result, "rb") as f:
                        st.download_button("📥 Download PDF", f, file_name=output_pdf)
                    pdf_viewer(output_pdf, width=700, height=1000, zoom_level=0.6)
                    cleanup(image_paths_dict)
                else:
                    st.error("Failed to create PDF.")
        else:
            st.warning("Please enter both URL and PDF name.")

# ---------- PAGE 2 ----------
elif choice == "📚 Multi-Chapter":
    st.title("📚 Manga Gari - Multi-Chapter PDF Builder")
    base_url = st.text_input("🔗 Base URL (replace chapter number with {})")
    start_ch = st.number_input("Start Chapter", min_value=1, value=1)
    end_ch = st.number_input("End Chapter (max 15 total)", min_value=1, value=1)
    pdf_name = st.text_input("📘 Output PDF name", "manga_volume")

    if st.button("Download Chapters"):
        chapter_count = end_ch - start_ch + 1
        if base_url and pdf_name and start_ch <= end_ch and chapter_count <= 15:
            image_paths_dict = {}
            with st.spinner("Downloading chapters..."):
                for ch in range(start_ch, end_ch + 1):
                    chapter_url = base_url.format(ch)
                    st.write(f"📥 Scraping Chapter {ch} ...")
                    paths = download_images(chapter_url, chapter=ch)
                    if paths:
                        image_paths_dict[ch] = paths
            output_pdf = f"{pdf_name}.pdf"
            result = images_to_pdf(image_paths_dict, output_pdf)

            if result:
                st.success("✅ PDF created!")
                with open(result, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name=output_pdf)
                pdf_viewer(output_pdf, width=700, height=1000, zoom_level=0.6)
                cleanup(image_paths_dict)
            else:
                st.error("No valid images to create PDF.")
        else:
            st.warning("⚠️ You can download a maximum of 15 chapters at once. Adjust the chapter range.")

# ---------- PAGE 3 ----------
elif choice == "❓ How to Use":
    st.title("📘 How to Use Manga Gari")

    st.markdown("""
### 👣 Steps to Use:
1. Go to the manga chapter you want.
2. Copy the chapter URL or the base URL.
3. Paste it into the input field.
   - For multi-chapter, replace the chapter number in the URL with `{}` (e.g., `https://readonepiece.com/manga/one-piece-chapter-{}`)
4. Enter output PDF name.
5. Click the button to generate and download.

---

### 🖥️ Supported Manga Sites

Here are some supported sites you can scrape from:
""")

    supported_sites = {
        "Ichi the Witch": "https://readichithewitch.com/",
        "Undead Unluck": "https://readundead.com/",
        "Sakamoto Days": "https://readsakadays.com/",
        "Kagurabachi": "https://readkagurabachimanga.com/",
        "Solo Leveling": "https://readsololeveling.org/",
        "One Piece": "https://readonepiece.com/",
        "Blue Lock": "http://bluelockread.com/",
        "Chainsaw Man": "https://readchainsawman.com/",
        "Black Clover": "http://readblackclover.com/",
        "Jujutsu Kaisen": "https://readjujutsukaisen.com/",
        "Demon Slayer": "https://demonslayermanga.com/",
        "Tokyo Revengers": "https://readtokyorevengers.net/",
        "Boruto": "https://ww8.readnaruto.com/manga/boruto-naruto-next-generations",
        "Naruto": "https://ww4.readnaruto.com/manga/naruto/",
        "Bleach": "https://readbleachmanga.com",
        "My Hero Academia": "https://readmha.com/",
        "Fairy Tail": "https://ww3.readfairytail.com/manga/fairy-tail/",
        "Haikyuu!!": "https://readhaikyuu.com/",
        "Vinland Saga": "https://readvinlandsaga.com/",
        "JoJo's Bizarre Adventure": "https://readjojos.com/"
    }

    for name, url in supported_sites.items():
        st.markdown(f"- [{name}]({url})")

    st.info("Manga Gari works best with sites that have direct <img> tags for manga panels on the chapter pages.")
