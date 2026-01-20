import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

app = Flask(__name__)

# DATABASE_URL Render сам добавит в Environment Variables
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Key(db.Model):
    __tablename__ = "keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    key_value: Mapped[str] = mapped_column(unique=True, nullable=False)
    is_used: Mapped[bool] = mapped_column(default=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return jsonify({"status": "online", "message": "Key system API работает!"})

@app.route('/check', methods=['POST'])
def check_key():
    try:
        data = request.json
        key_val = data.get('key')
        if not key_val:
            return jsonify({'valid': False, 'message': 'Missing key'}), 400

        key_obj = Key.query.filter_by(key_value=key_val, is_used=False).first()
        if key_obj:
            key_obj.is_used = True
            db.session.commit()
            return jsonify({'valid': True, 'message': 'Ключ активирован!'})
        return jsonify({'valid': False, 'message': 'Неверный или использованный ключ'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'valid': False, 'message': str(e)}), 500

@app.route('/add_keys', methods=['POST'])
def add_keys():
    try:
        data = request.json
        new_keys = data.get('keys', [])
        added = 0
        for k in new_keys:
            if not Key.query.filter_by(key_value=k).first():
                db.session.add(Key(key_value=k))
                added += 1
        db.session.commit()
        return jsonify({'success': True, 'added': added})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
