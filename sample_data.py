from .db import SessionLocal
from .crud import create_project, create_shift, create_agent
from datetime import datetime

def seed():
    db = SessionLocal()
    p1 = create_project(db, type("P", (), {"name":"Project 1","max_agents":80,"off_pattern":None}))
    create_shift(db, p1.id, type("S", (), {"name":"Morning","start_time":"07:00","end_time":"16:00","crosses_midnight":False,"shift_order":0}))
    create_shift(db, p1.id, type("S", (), {"name":"Afternoon","start_time":"15:00","end_time":"00:00","crosses_midnight":True,"shift_order":1}))
    create_shift(db, p1.id, type("S", (), {"name":"Night","start_time":"23:00","end_time":"08:00","crosses_midnight":True,"shift_order":2}))

    p2 = create_project(db, type("P", (), {"name":"Project 2","max_agents":80,"off_pattern":"fri_sat"}))
    create_shift(db, p2.id, type("S", (), {"name":"Morning","start_time":"06:30","end_time":"15:30","crosses_midnight":False,"shift_order":0}))
    create_shift(db, p2.id, type("S", (), {"name":"Afternoon","start_time":"13:30","end_time":"22:30","crosses_midnight":True,"shift_order":1}))
    create_shift(db, p2.id, type("S", (), {"name":"Night","start_time":"21:30","end_time":"06:30","crosses_midnight":True,"shift_order":2}))

    for i in range(1,48):
        skill = 'both' if i%3==0 else ('chat' if i%2==0 else 'email')
        create_agent(db, p1.id, type("A", (), {"name":f"P1-Agent-{i}", "email":None, "channel_skill":skill}))
    for i in range(1,72):
        skill = 'both' if i%4==0 else ('chat' if i%2==0 else 'email')
        create_agent(db, p2.id, type("A", (), {"name":f"P2-Agent-{i}", "email":None, "channel_skill":skill}))
    print("Seeded Projects & agents.")

if __name__ == "__main__":
    seed()
