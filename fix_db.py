import sqlite3

def rebalance():
    try:
        # Подключаемся к твоей базе
        conn = sqlite3.connect('baysard_final.db')
        cursor = conn.cursor()
        
        print("Начинаю магию перерасчета...")
        
        # Выполняем тот самый SQL запрос
        cursor.execute("""
            UPDATE students 
            SET 
                knowledge = CAST(knowledge * 0.7 AS INTEGER), 
                leadership = CASE WHEN leadership < 80 THEN leadership + 15 ELSE leadership END,
                discipline = CASE WHEN discipline < 80 THEN discipline + 20 ELSE discipline END;
        """)
        
        conn.commit()
        conn.close()
        print("✨ Готово! Баланс восстановлен. Теперь можешь запускать app.py")
        
    except Exception as e:
        print(f"Ой, что-то пошло не так: {e}")

if __name__ == "__main__":
    rebalance()
