import sqlite3

c = sqlite3.connect('dev.db')

cols = [r[1] for r in c.execute("PRAGMA table_info(chat_message)")]
print("当前列:", cols)

if 'image_url' not in cols:
    c.execute("ALTER TABLE chat_message ADD COLUMN image_url TEXT")
    c.commit()
    print("✅ image_url 列已添加")
else:
    print("ℹ️ image_url 列已存在")

print("修改后列:", [r[1] for r in c.execute("PRAGMA table_info(chat_message)")])
c.close()