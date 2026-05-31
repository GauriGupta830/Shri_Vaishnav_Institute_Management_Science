import os
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from college_data import COLLEGE_INFO

SVIM_PAGES = [
    "https://www.svimi.org",
    "https://www.svimi.org/placement/about-placement.php",
    "https://www.svimi.org/placement/recruiters.php",
    "https://www.svimi.org/placement/prominent-selections.php",
    "https://www.svimi.org/infrastructure/library.php",
    "https://www.svimi.org/infrastructure/hostel.php",
    "https://www.svimi.org/infrastructure/canteen.php",
    "https://www.svimi.org/infrastructure/sports.php",
    "https://www.svimi.org/under-graduate.php",
    "https://www.svimi.org/post-graduate.php",
    "https://www.svimi.org/fee-structure.php",
    "https://www.svimi.org/scholarship.php",
    "https://www.svimi.org/admission-process.php",
    "https://www.svimi.org/activity-clubs/it-club.php",
    "https://www.svimi.org/activity-clubs/finance-club.php",
    "https://www.svimi.org/activity-clubs/literary-club.php",
    "https://www.svimi.org/activity-clubs/hr-club.php",
    "https://www.svimi.org/activity-clubs/marketing-club.php",
    "https://www.svimi.org/activity-clubs/science-club.php",
    "https://www.svimi.org/activity-clubs/photography-club.php",
    "https://www.svimi.org/cells/nss.php",
    "https://www.svimi.org/cells/edc.php",
    "https://www.svimi.org/cells/iic.php",
    "https://www.svimi.org/cells/rdc.php",
    "https://www.svimi.org/contact-us.php",
    "https://www.svimi.org/TelephoneDirectory.php",
    "https://www.svimi.org/about-institute-description.php",
    "https://www.svimi.org/vision.php",
    "https://www.svimi.org/leadership.php?q=director",
    "https://www.svimi.org/leadership.php?q=chairman",
    "https://www.svimi.org/leadership.php?q=patron",
    "https://www.svimi.org/departments/faculties.php?q=faculty_cs",
    "https://www.svimi.org/departments/faculties.php?q=faculty_UG",
    "https://www.svimi.org/departments/faculties.php?q=faculty_PG",
    "https://www.svimi.org/governing-body.php",
    "https://www.svimi.org/committees.php",
    "https://www.svimi.org/TelephoneDirectory.php",
]

def read_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        print(f"✅ PDF padha: {pdf_path}")
    except Exception as e:
        print(f"❌ PDF error {pdf_path}: {e}")
    return text

def read_all_pdfs(folder_path="college_docs"):
    all_text = ""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return ""
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    if not pdf_files:
        print("⚠️ No PDFs found")
        return ""
    print(f"📄 {len(pdf_files)} PDFs found!")
    for pdf_file in pdf_files:
        text = read_pdf(os.path.join(folder_path, pdf_file))
        if text:
            all_text += f"\n\n=== PDF: {pdf_file} ===\n{text}"
    return all_text

def scrape_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        text = ' '.join(soup.get_text().split())
        print(f"✅ Scraped: {url}")
        return f"\n\n=== FROM: {url} ===\n{text[:4000]}"
    except Exception as e:
        print(f"❌ Error {url}: {e}")
        return ""

def scrape_contact_directory():
    """Faculty aur contacts scrape karo"""
    print("📋 Contact directory scrape ho rahi hai...")
    contact_text = "\n\n=== CONTACT DIRECTORY ===\n"
    urls = [
        "https://www.svimi.org/TelephoneDirectory.php",
        "https://www.svimi.org/departments/faculties.php?q=faculty_cs",
        "https://www.svimi.org/departments/faculties.php?q=faculty_UG",
        "https://www.svimi.org/departments/faculties.php?q=faculty_PG",
        "https://www.svimi.org/leadership.php?q=director",
        "https://www.svimi.org/contact-us.php",
    ]
    for url in urls:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            text = ' '.join(soup.get_text().split())
            contact_text += f"\nFrom {url}:\n{text[:3000]}\n"
            print(f"✅ Contact scraped: {url}")
        except Exception as e:
            print(f"❌ Contact error: {e}")
    return contact_text

def create_knowledge_base(college_url=None):
    print("🔄 Knowledge base ban raha hai...")
    print("=" * 50)

    print("📚 Source 1: Manual college data...")
    all_text = "=== SVIMS MANUAL DATA ===\n" + COLLEGE_INFO

    print("\n📄 Source 2: PDFs...")
    pdf_text = read_all_pdfs("college_docs")
    if pdf_text:
        all_text += "\n\n=== PDF DATA ===\n" + pdf_text

    print("\n📋 Source 3: Contact Directory...")
    contact_text = scrape_contact_directory()
    all_text += contact_text

    print("\n🌐 Source 4: Website scraping...")
    web_text = ""
    for url in SVIM_PAGES:
        web_text += scrape_page(url)
    all_text += "\n\n=== WEBSITE DATA ===\n" + web_text

    print(f"\n📝 Total: {len(all_text)} characters")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_text(all_text)
    print(f"✅ {len(chunks)} chunks")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")
    print("✅ Knowledge base ready!")
    return vector_store

def load_knowledge_base():
    if os.path.exists("faiss_index"):
        print("📂 Loading existing knowledge base...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        return FAISS.load_local(
            "faiss_index",
            embeddings,
            allow_dangerous_deserialization=True
        )
    return None