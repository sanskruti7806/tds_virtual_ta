import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import openai

from fastapi.middleware.cors import CORSMiddleware

# Load OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Allow requests from any origin (important if deployed with a front-end)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class Link(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[Link]

def load_course_content() -> str:
    text = ""
    folder = "data/course_content"
    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
                text += f.read() + "\n"
    return text

def load_discourse_posts() -> List[dict]:
    path = "data/discourse_posts.json"
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def search_posts(question: str, posts: List[dict]) -> List[dict]:
    matches = []
    for post in posts:
        if question.lower() in post["content"].lower() or question.lower() in post["title"].lower():
            matches.append(post)
    return matches[:2]  # Return top 2 matches

@app.post("/", response_model=AnswerResponse)
async def answer_question(payload: QuestionRequest):
    course_content = load_course_content()
    discourse_posts = load_discourse_posts()
    matched_posts = search_posts(payload.question, discourse_posts)

    context = course_content + "\n\n"
    for post in matched_posts:
        context += f"Title: {post['title']}\nContent: {post['content']}\n\n"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Teaching Assistant for the TDS course."},
                {"role": "user", "content": f"Answer the following student question based on course notes and posts:\n\n{context}\n\nQuestion: {payload.question}"}
            ],
            temperature=0.4,
        )
        answer = response["choices"][0]["message"]["content"]
    except Exception as e:
        return {"answer": f"Failed to fetch answer: {str(e)}", "links": []}

    links = [{"url": post["link"], "text": post["content"][:80]} for post in matched_posts]

    return {
        "answer": answer,
        "links": links
    }
