import random
 
N = 10_000_000
days = range(7)
qualifies = other_is_girl = 0
 
for _ in range(N):
    c1 = (random.randint(0,1), random.choice(days))
    c2 = (random.randint(0,1), random.choice(days))
    if (c1[0]==1 and c1[1]==1) or (c2[0]==1 and c2[1]==1):
        qualifies += 1
        if (c1[0]==0 or c2[0]==0):
            other_is_girl += 1
 
print(f"{other_is_girl/qualifies:.4f}")
