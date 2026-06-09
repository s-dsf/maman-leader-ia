import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def lancer_agent(role_key, instruction, prompts, contexte=""):
    if role_key in prompts and role_key != "agents_custom":
        p = prompts[role_key]
    else:
        p = next((a for a in prompts.get("agents_custom", [])
                  if a["id"] == role_key), None)
        if not p:
            return "Agent introuvable."

    system_prompt = f"""Tu es {p['nom']}, {p['role']}.

{p['backstory']}

Tes tâches :
{p['taches']}

Tu travailles pour la maison éditoriale Maman & Leader.
Leadership féminin incarné, responsabilité sans dureté,
structure sans rigidité, douceur sans effacement."""

    user_message = instruction
    if contexte:
        user_message = f"CONTEXTE :\n{contexte}\n\n{instruction}"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    return message.content[0].text