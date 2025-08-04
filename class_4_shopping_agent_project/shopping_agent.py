
import os
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich import print

# Import OpenAI library components
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageToolCall

# Load environment variables
load_dotenv()

# Get API key from .env
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in your .env file.")

# Initialize Rich Console for pretty printing
console = Console()

# --- 1. Define the Tool(s) ---

# This function will be called by the agent when it decides it needs product data.
# The docstring and parameter types are crucial for the LLM to understand the tool.
def get_products_api(query: str = None):
    """
    Fetch a list of products from an online API.
    Can optionally filter products by a search query against product name, description, or category.

    Args:
        query (str, optional): A keyword or phrase to search for in product names, descriptions, or categories.
                                If None, returns all available products.
    Returns:
        dict: A dictionary containing product data or an error message.
              Expected format: {"data": [...]} or {"error": "..."}
    """
    url = "https://template-03-api.vercel.app/api/products"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if "data" not in data or not isinstance(data["data"], list):
            return {"error": "API response format invalid: missing 'data' key or not a list.", "raw_response": data}

        products = data["data"]

        if query:
            query_lower = query.lower()
            filtered_products = []
            for product in products:
                searchable_text = " ".join([
                    product.get("productName", ""),
                    product.get("description", ""),
                    product.get("category", "")
                ]).lower()
                if query_lower in searchable_text:
                    filtered_products.append(product)
            products = filtered_products

        return {"data": products} # Return filtered data or all data if no query
    except requests.RequestException as e:
        return {"error": f"Failed to fetch products from API: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

# --- 2. Initialize the OpenAI Client ---

# Use the actual OpenAI client, configured for Gemini via base_url
client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# --- 3. Define the Agent's Behavior (System Prompt) ---

# This is where we instruct the LLM on its role and how to use the tool.
SYSTEM_PROMPT = """You are a helpful shopping assistant. Your primary goal is to assist users in finding products.
You have access to a `get_products_api` tool to fetch product information.

When a user asks for products:
1. Call the `get_products_api` tool to get product data.
2. If the user's query contains keywords (like product names, types, or categories), pass that as the 'query' argument to the tool.
3. If no specific product is mentioned, you can call the tool without a 'query' to list general products.
4. Once you have the product data, present up to 5 relevant products to the user.
5. For each product, display its 'productName', 'price' (convert cents to dollars, e.g., 10000 becomes $100.00), and optionally 'description' or 'category' if relevant to the user's query.
6. If no products are found for a specific query, politely inform the user and perhaps suggest some general popular products.
7. Be friendly, concise, and always offer further assistance.
"""

# --- 4. Define Tools for the OpenAI Client ---

# This tells the OpenAI client about the available tools and their schemas.
# The 'function' part describes how to call the Python function.
available_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_products_api",
            "description": "Fetch a list of products from an online store, optionally filtered by a search query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A keyword or phrase to search for within product names, descriptions, or categories (e.g., 'shoes', 'watch', 'electronics')."
                    }
                },
                "required": [], # Query is optional, so not required
            },
        },
    }
]

# --- 5. Main Agent Interaction Loop ---

def run_shopping_agent():
    console.print(Panel("[bold green]Welcome to the AI Shopping Assistant![/bold green]", expand=False))
    console.print("Type your product request (e.g., 'I need running shoes', 'show me all products', 'wireless headphones under $100').")
    console.print("Type 'exit' or 'quit' to end the chat.\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = console.input("[bold cyan]You:[/bold cyan] ")
        if user_input.strip().lower() in ("exit", "quit"):
            console.print(Panel("[bold yellow]Thank you for using the Shopping Assistant. Goodbye![/bold yellow]", expand=False))
            break

        messages.append({"role": "user", "content": user_input})
        console.print("[bold magenta]Agent thinking...[/bold magenta]")

        try:
            # Step 1: Send user query and available tools to the LLM
            response = client.chat.completions.create(
                model="gemini-1.5-flash-latest", # Using the latest flash model
                messages=messages,
                tools=available_tools,
                tool_choice="auto" # Let the model decide if and which tool to call
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Step 2: Check if the LLM wants to call a tool
            if tool_calls:
                # Add the tool call request from the LLM to messages history
                messages.append(response_message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = tool_call.function.arguments

                    # Execute the tool (only get_products_api in this case)
                    if function_name == "get_products_api":
                        try:
                            # Parse args from LLM (it's a JSON string)
                            import json
                            args = json.loads(function_args)
                            tool_output = get_products_api(**args)
                            tool_output_str = json.dumps(tool_output, indent=2) # Pretty print tool output
                            console.print(f"[dim]Tool Call: {function_name}({function_args})[/dim]")
                            console.print(f"[dim]Tool Output: {tool_output_str}[/dim]")

                            # Step 3: Send tool output back to the LLM for a final response
                            messages.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": tool_output_str,
                                }
                            )
                            # Get the final response from the LLM
                            final_response = client.chat.completions.create(
                                model="gemini-1.5-flash-latest",
                                messages=messages
                            )
                            agent_response_content = final_response.choices[0].message.content
                            messages.append({"role": "assistant", "content": agent_response_content})
                            console.print(Panel(f"[green]Agent:[/green] {agent_response_content}", border_style="green"))

                        except json.JSONDecodeError:
                            error_message = f"Agent tried to call {function_name} with invalid JSON arguments: {function_args}"
                            console.print(f"[bold red]Error:[/bold red] {error_message}")
                            messages.append({"role": "assistant", "content": f"I encountered an error processing your request: {error_message}"})
                        except Exception as e:
                            error_message = f"Error executing tool {function_name}: {e}"
                            console.print(f"[bold red]Error:[/bold red] {error_message}")
                            messages.append({"role": "assistant", "content": f"I encountered an error while trying to find products: {e}"})
                    else:
                        console.print(f"[bold red]Error:[/bold red] Unknown tool requested by agent: {function_name}")
                        messages.append({"role": "assistant", "content": f"I was asked to use an unknown tool ({function_name}). Please try again or rephrase your request."})
            else:
                # If no tool call, it means the LLM can respond directly (e.g., greetings, unanswerable questions)
                agent_response_content = response_message.content
                messages.append({"role": "assistant", "content": agent_response_content})
                console.print(Panel(f"[green]Agent:[/green] {agent_response_content}", border_style="green"))

        except Exception as e:
            console.print(Panel(f"[bold red]An unexpected error occurred:[/bold red] {e}", border_style="red"))
            messages.append({"role": "assistant", "content": "I apologize, but I encountered an error. Could you please try again?"})


if __name__ == "__main__":
    run_shopping_agent()



