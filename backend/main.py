from fastapi import FastAPI
from pydantic import BaseModel
from bs4 import BeautifulSoup
from groq import Groq
import requests
import os
from dotenv import load_dotenv

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
# WEB SCRAPER FUNCTION
# --------------------------------
def scrape_products():

    url = "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    products = []

    items = soup.find_all("div", class_="thumbnail")

    for item in items:

        # Product Name
        name = item.find("a", class_="title").text.strip()

        # Product Price
        price = item.find("h4", class_="price").text.strip()

        # Product Description
        description = item.find("p", class_="description").text.strip()

        # Rating
        rating = len(item.find_all("span", class_="glyphicon-star"))

        # Reviews
        review_tag = item.find("p", class_="pull-right")
        reviews = review_tag.text.strip() if review_tag else "No reviews"

        # Store product
        products.append({
            "name": name,
            "price": price,
            "description": description,
            "rating": rating,
            "reviews": reviews
        })

    return products


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
    # STEP 1: SCRAPE PRODUCTS
    # --------------------------------
    products = scrape_products()

    products = products[:5]

    # --------------------------------
    # STEP 2: CREATE AI PROMPT
    # --------------------------------
    prompt = f"""
    User Query:
    {query.text}

    Here are the scraped products:

    {products}

    Analyze the products carefully.

    Recommend the best products for the user based on:
    - budget
    - performance
    - use case

    Explain:
    - which product is best
    - why it is suitable
    - which products should be avoided

    Keep the response concise.
    """

    # --------------------------------
    # STEP 3: AI REASONING
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
    # STEP 4: RETURN RESPONSE
    # --------------------------------
    return {
        "user_query": query.text,
        "total_products_scraped": len(products),
        "ai_recommendation": ai_response
    }