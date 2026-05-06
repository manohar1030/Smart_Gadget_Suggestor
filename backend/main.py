from fastapi import FastAPI
from pydantic import BaseModel
from bs4 import BeautifulSoup
from groq import Groq
import requests
import os
from dotenv import load_dotenv

# --------------------------------
# LOAD ENV VARIABLES
# --------------------------------
load_dotenv()

app = FastAPI()

# --------------------------------
# GROQ CLIENT
# --------------------------------
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# --------------------------------
# REQUEST MODEL
# --------------------------------
class Query(BaseModel):
    text: str


# --------------------------------
# SMART SCRAPER
# --------------------------------
def scrape_products(user_query):

    url = "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    products = []

    items = soup.find_all("div", class_="thumbnail")

    # --------------------------------
    # USER INTENT
    # --------------------------------
    query = user_query.lower()

    # --------------------------------
    # DYNAMIC KEYWORDS
    # --------------------------------
    if "gaming" in query:

        keywords = [
            "gtx",
            "rtx",
            "rog",
            "nitro",
            "legion",
            "gaming",
            "ryzen",
            "i7"
        ]

    elif "student" in query:

        keywords = [
            "ssd",
            "portable",
            "light",
            "thin"
        ]

    elif "coding" in query or "programming" in query:

        keywords = [
            "i5",
            "i7",
            "16gb",
            "ssd"
        ]

    else:

        keywords = []

    # --------------------------------
    # SCRAPE PRODUCTS
    # --------------------------------
    for item in items:

        # Name
        name_tag = item.find("a", class_="title")
        name = name_tag.text.strip() if name_tag else "No name"

        # Price
        price_tag = item.find("h4", class_="price")
        price = price_tag.text.strip() if price_tag else "$0"

        # Description
        desc_tag = item.find("p", class_="description")
        description = desc_tag.text.strip() if desc_tag else "No description"

        # Rating
        rating = len(item.find_all("span", class_="glyphicon-star"))

        # Reviews
        review_tag = item.find("p", class_="pull-right")
        reviews = review_tag.text.strip() if review_tag else "No reviews"

        # --------------------------------
        # SMART RETRIEVAL
        # --------------------------------
        if keywords:

            if not any(word in description.lower() for word in keywords):
                continue

        products.append({
            "name": name,
            "price": price,
            "description": description,
            "rating": rating,
            "reviews": reviews
        })

    return products


# --------------------------------
# FILTER + SCORE PRODUCTS
# --------------------------------
def filter_and_score_products(products, user_query):

    ranked_products = []

    query = user_query.lower()

    for p in products:

        desc = p["description"].lower()

        score = 0

        # --------------------------------
        # REMOVE WEAK LAPTOPS
        # --------------------------------
        bad_keywords = ["celeron", "pentium"]

        if any(word in desc for word in bad_keywords):
            continue

        # =========================================
        # GAMING LAPTOP SCORING
        # =========================================
        if "gaming" in query:

            if "gtx" in desc:
                score += 10

            if "rtx" in desc:
                score += 15

            if "i5" in desc:
                score += 5

            if "i7" in desc:
                score += 8

            if "ryzen 5" in desc:
                score += 7

            if "ryzen 7" in desc:
                score += 10

            if "16gb" in desc:
                score += 6

            if "8gb" in desc:
                score += 3

            if "ssd" in desc:
                score += 4

        # =========================================
        # STUDENT LAPTOP SCORING
        # =========================================
        elif "student" in query:

            if "ssd" in desc:
                score += 5

            if '13.3"' in desc:
                score += 3

            if '14"' in desc:
                score += 3

            if "i3" in desc:
                score += 3

            if "i5" in desc:
                score += 5

        # =========================================
        # CODING LAPTOP SCORING
        # =========================================
        elif "coding" in query or "programming" in query:

            if "i5" in desc:
                score += 5

            if "i7" in desc:
                score += 8

            if "16gb" in desc:
                score += 8

            if "8gb" in desc:
                score += 4

            if "ssd" in desc:
                score += 5

        # =========================================
        # GENERAL SCORING
        # =========================================
        else:

            if "i5" in desc:
                score += 4

            if "i7" in desc:
                score += 6

            if "ssd" in desc:
                score += 3

        # Save score
        p["score"] = score

        ranked_products.append(p)

    # --------------------------------
    # SORT PRODUCTS
    # --------------------------------
    ranked_products.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return ranked_products


# --------------------------------
# HOME ROUTE
# --------------------------------
@app.get("/")
async def home():
    return {
        "message": "AI Smart Product Agent Running"
    }


# --------------------------------
# RECOMMENDATION ROUTE
# --------------------------------
@app.post("/recommend")
async def recommend(query: Query):

    # --------------------------------
    # STEP 1: SMART SCRAPING
    # --------------------------------
    products = scrape_products(query.text)

    print("SCRAPED PRODUCTS:", len(products))

    # --------------------------------
    # STEP 2: FILTER + SCORE
    # --------------------------------
    ranked_products = filter_and_score_products(
        products,
        query.text
    )

    # --------------------------------
    # STEP 3: TOP PRODUCTS
    # --------------------------------
    top_products = ranked_products[:5]

    print("TOP PRODUCTS:", top_products)

    # --------------------------------
    # STEP 4: AI PROMPT
    # --------------------------------
    prompt = f"""
    User Query:
    {query.text}

    Here are the top ranked products:

    {top_products}

    Analyze the products carefully.

    Recommend:
    - best overall product
    - why it is suitable
    - pros and cons
    - best value for money

    Keep response concise.
    """

    # --------------------------------
    # STEP 5: AI REASONING
    # --------------------------------
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    ai_response = response.choices[0].message.content

    print(ai_response)

    # --------------------------------
    # STEP 6: RETURN RESPONSE
    # --------------------------------
    return {
        "user_query": query.text,
        "scraped_products_count": len(products),
        "top_products": top_products,
        "ai_recommendation": ai_response
    }