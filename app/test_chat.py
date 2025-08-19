from app.chat import recommend

q = "vreau o carte despre prietenie si magie"
print("Q:", q)
print(recommend(q, top_k=4))
