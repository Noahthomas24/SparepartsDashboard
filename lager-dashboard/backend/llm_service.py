import os
import requests


def generate_inventory_insight(
    analyse_data: list[dict], user_question: str = ""
) -> dict:

    # henter API-nøglen fra miljøvariablerne
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "MISTRAL_API_KEY mangler i miljøvariablerne.",
        }

    # Formatérer dataen, så AI'en nemt kan læse den
    sorted_by_forbrug = sorted(
        analyse_data, key=lambda x: x["total_usage"], reverse=True
    )[:4]

    data_summary = "Lagerdata overblik (Top 4):\n"
    for item in sorted_by_forbrug:
        data_summary += (
            f"- {item['product_id']}: Forbrugt {item['total_usage']} stk. \n"
        )

    # system prompts
    system_prompt = (
        "Du er en skarp og analytisk logistikassistent. "
        "Giv konkrete råd om indkøbsstrategier baseret på disse lagerdata. "
        "Fremhæv mønstre, advarsler om mulige mangler, og hold det henvendt til en lagermedarbejder."
    )

    # Opbygger selve spørgsmålet (User Prompt)
    user_prompt = f"Her er min data:\n{data_summary}\n"
    if user_question:
        user_prompt += f"\nBrugerens specifikke spørgsmål: {user_question}"
    else:
        user_prompt += "\nHvilke 3 dele bør vi overvåge tættest, og hvordan kan vi optimere indkøbet af dem?"

    # Klargør API-kaldet
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": "mistral-small-latest",  # hurtig
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,  # Lav temperatur = mere analytiske og faktuelle svar
    }

    try:
        # Send data til Mistral
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload
        )
        response.raise_for_status()  # Kaster en fejl, hvis HTTP-status ikke er 2xx

        # Udpak teksten fra JSON-svaret
        ai_text = response.json()["choices"][0]["message"]["content"]
        return {"status": "success", "text": ai_text}

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Netværksfejl eller afvist af API: {str(e)}",
        }
    except KeyError:
        return {
            "status": "error",
            "message": "Kunne ikke læse svaret fra Mistral. Uventet JSON-struktur.",
        }
