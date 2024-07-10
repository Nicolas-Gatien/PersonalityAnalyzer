import anthropic
import json
import numpy as np
import matplotlib.pyplot as plt
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

with open("config.json", "r") as file:
    config = json.load(file)
    api_key = config.get("API-KEY")

# Define colors
colors = ['blue', 'orange', 'green', 'red', 'purple']

def create_personality_flower(dimensions, scores):
    """
    Create a personality flower visualization of the PRISM framework scores.
    
    This function generates a flower-like chart where each dimension is
    represented by a petal, and the score determines the length of the petal.
    
    Args:
    dimensions (list): List of dimension names
    scores (list): Corresponding scores for each dimension
    """
    # Assign colors before filtering
    dim_colors = []
    for i, dim in enumerate(dimensions):
        color_index = i // 10  # Determines which color to use
        color = colors[color_index % len(colors)]  # Wraps around if more than available colors
        dim_colors.append(color)
    
    # Filter out dimensions, scores, and colors that are equal to 0
    filtered_data = [(dim, score, color) for dim, score, color in zip(dimensions, scores, dim_colors) if score != 0]
    
    if not filtered_data:
        print("No valid scores to display.")
        return

    filtered_dimensions, filtered_scores, filtered_colors = zip(*filtered_data)

    N = len(filtered_dimensions)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False)
    
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))
    
    # Create each petal
    for angle, score, dimension, color in zip(angles, filtered_scores, filtered_dimensions, filtered_colors):
        # Generate points for a petal shape
        petal_angles = np.linspace(angle - 0.1, angle + 0.1, 100)
        petal_distances = np.array([score * np.sin(x) for x in np.linspace(0, np.pi, 100)])
        
        # Plot and fill the petal
        ax.plot(petal_angles, petal_distances, color=color)
        ax.fill(petal_angles, petal_distances, color=color, alpha=0.1)
        
        # Add dimension labels
        ax.text(angle, score+0.5, dimension, ha='center', va='center')
    
    ax.set_yticklabels([])  # Remove radial labels
    
    plt.title("2. PRISM Personality Flower", size=20, y=1.1)
    
    plt.tight_layout()
    plt.savefig("2_personality_flower.png")
    plt.close()


anthropic_client = anthropic.Anthropic(api_key=api_key)

context = [{"role": "user", "content": "Probe the user with questions and scenarios that reveal details about their personality. Only ask one question at a time. Be direct and to the point. Go on tangents and dig deeper into the answers the user provides."}]

def get_response():
    response = anthropic_client.messages.create(
        max_tokens=300,
        model="claude-3-5-sonnet-20240620",
        messages=context
    )
    context.append({"role": "assistant", "content": response.content[0].text})

def transcript(loaded=True):
    global context
    transcript: str = ""
    if loaded:
        with open("transcript.json", 'r') as file:
            context = json.loads(file.read())
    for message in context:
        transcript += f"{message['role']}: {message['content']}\n"
    return transcript
while True:
    get_response()
    print(Fore.YELLOW + context[-1]["content"])
    prompt = input("")
    if prompt.lower() == "exit":
        with open("transcript.json", 'w') as file:
            file.write(json.dumps(context, indent=4))
        break
    context.append({"role": "user", "content": prompt})

print(transcript())
transcript = transcript()

categories = [
"""
[0] Cognitive Flexibility (rigid to adaptable)
[1] Openness to Experience (conventional to exploratory)
[2] Creativity (practical to innovative)
[3] Cognitive Processing Style (analytical to intuitive)
[4] Need for Cognition (low to high engagement in cognitive activities)
[5] Dialectical Thinking (absolutist to dialectical)
[6] Ambiguity Tolerance (low to high comfort with uncertainty)
[7] Time Perspective (past-oriented to future-oriented)
[8] Decision-Making Style (impulsive to deliberative)
[9] Psychological Entropy (low to high capacity for managing uncertainty)
""",
"""
[0] Emotional Intelligence (low to high)
[1] Neuroticism (emotionally stable to volatile)
[2] Emotional Regulation (reactive to composed)
[3] Empathy (detached to highly empathetic)
[4] Emotional Expressiveness (reserved to expressive)
[5] Emotional Granularity (low to high differentiation of emotions)
[6] Sensory Processing Sensitivity (low to high sensitivity)
[7] Optimism vs. Pessimism (pessimistic to optimistic)
[8] Stress Response (overwhelmed to resilient)
[9] Self-Esteem (low to high)
""",
"""
[0] Extraversion (introverted to extraverted)
[1] Agreeableness (competitive to cooperative)
[2] Social Orientation (individualistic to collectivistic)
[3] Cultural Adaptability (rigid to adaptable)
[4] Assertiveness (passive to assertive)
[5] Trust Propensity (cautious to trusting)
[6] Attachment Style (insecure to secure)
[7] Cultural Tightness-Looseness (loose to tight)
[8] Social Dominance Orientation (egalitarian to hierarchical)
[9] Digital Personality (offline-centric to online-centric)
""",
"""
[0] Conscientiousness (spontaneous to organized)
[1] Self-Awareness (low to high)
[2] Resilience (fragile to resilient)
[3] Growth Mindset (fixed to growth-oriented)
[4] Impulse Control (impulsive to restrained)
[5] Grit (low to high persistence)
[6] Mindfulness (inattentive to mindful)
[7] Delay of Gratification (immediate to delayed gratification)
[8] Work-Life Balance (work-centric to life-centric)
[9] Perfectionism (relaxed to perfectionistic)
""",
"""
[0] Moral Foundation (intuitive to principled)
[1] Achievement Orientation (contented to ambitious)
[2] Risk Tolerance (risk-averse to risk-seeking)
[3] Locus of Control (external to internal)
[4] Curiosity (incurious to curious)
[5] Self-Efficacy (low to high belief in capabilities)
[6] Honesty-Humility (manipulative to sincere)
[7] Adaptability to Change (resistant to embracing)
[8] Self-Complexity (simple to complex self-concept)
[9] Authenticity (conforming to authentic)
"""
]

ratings = []
for category in categories:
    rating_prompt = f"""Rate the user from 1-10 in each of the following 10 categories:
<<<
{category}
>>>

    Here is a transcript between the user and the assistant, use this transcript to inform the scores you give to the user.
<<<
{transcript}
>>>
    If you feel you don't have enough information to properly rate a specific axis, rate it a 0.
    Do not include any text other than the following:
    Only output a single JSON dictionary that looks like the following:
    {{
    "ratings": [<int>, <int>, <int>, <int>, <int>, <int>, <int>, <int>, <int>, <int>]
    }}
    """
    response = anthropic_client.messages.create(
        max_tokens=300,
        model="claude-3-5-sonnet-20240620",
        messages=[{"role": "user", "content": rating_prompt}]
    )
    try:
        loaded = json.loads(response.content[0].text)["ratings"]
    except:
        response = anthropic_client.messages.create(
            max_tokens=300,
            model="claude-3-5-sonnet-20240620",
            messages=[{"role": "user", "content": f"Fix this so that it is valid JSON code. ONLY OUTPUT VALID JSON CODE: {response.content[0].text}"}]
        )

        loaded = json.loads(response.content[0].text)["ratings"]

    ratings.extend(loaded)

dimensions = [
    "Cognitive Flexibility", "Openness to Experience", "Creativity", "Cognitive Processing Style",
    "Need for Cognition", "Dialectical Thinking", "Ambiguity Tolerance", "Time Perspective",
    "Decision-Making Style", "Psychological Entropy", "Emotional Intelligence", "Neuroticism",
    "Emotional Regulation", "Empathy", "Emotional Expressiveness", "Emotional Granularity",
    "Sensory Processing Sensitivity", "Optimism vs. Pessimism", "Stress Response", "Self-Esteem",
    "Extraversion", "Agreeableness", "Social Orientation", "Cultural Adaptability",
    "Assertiveness", "Trust Propensity", "Attachment Style", "Cultural Tightness-Looseness",
    "Social Dominance Orientation", "Digital Personality", "Conscientiousness", "Self-Awareness",
    "Resilience", "Growth Mindset", "Impulse Control", "Grit", "Mindfulness", "Delay of Gratification",
    "Work-Life Balance", "Perfectionism", "Moral Foundation", "Achievement Orientation", "Risk Tolerance",
    "Locus of Control", "Curiosity", "Self-Efficacy", "Honesty-Humility", "Adaptability to Change",
    "Self-Complexity", "Authenticity"
]
print(ratings)
create_personality_flower(dimensions, ratings)
