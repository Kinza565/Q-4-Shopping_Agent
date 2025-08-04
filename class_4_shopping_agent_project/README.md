# 🛍️ AI Shopping Agent – OpenAI + Product API Integration

This project is a **command-line based AI Shopping Assistant** built with the OpenAI Agents Framework. The assistant uses natural language to help users find relevant products by querying a live API.

---

## 🚀 Features

- 💬 Conversational interface (via terminal) powered by OpenAI's `gemini-1.5-flash-latest`
- 🔍 Product data fetched dynamically using `get_products_api` tool
- 🧠 Smart filtering by keyword, category, and description
- 💵 Prices automatically converted from cents to dollars
- 🚫 Handles API errors and no-result scenarios gracefully
- 🎨 Beautiful command-line UI using [Rich](https://github.com/Textualize/rich)

---

## 🛠️ Tech Stack

| Component         | Details                                  |
|------------------|-------------------------------------------|
| Language          | Python 3                                  |
| LLM Model         | `gemini-1.5-flash-latest` via OpenAI-style client |
| Tool Calling      | OpenAI Agents function call integration   |
| Product API       | [template-03-api](https://template-03-api.vercel.app/api/products) |
| CLI Interface     | [Rich](https://github.com/Textualize/rich) |
| Secrets Management| `python-dotenv` to load `.env` variables  |





