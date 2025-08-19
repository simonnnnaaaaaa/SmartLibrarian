from app.chat import recommend_with_summary

q = "vreau o carte despre prietenie si magie"
print("Q:", q)
print(recommend_with_summary(q, top_k=4))
