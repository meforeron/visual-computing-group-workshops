import os
import json
import shutil
from app import app, db
from models import User, Invoice

def populate():
    with app.app_context():
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            print("Error: Usuario 'demo' no encontrado.")
            return
        
        # Clear existing invoices to avoid duplicates
        Invoice.query.filter_by(user_id=demo_user.id).delete()
        db.session.commit()
        
        receipts_dir = 'receipts'
        uploads_dir = os.path.join('static', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # 1. Load from eval_report.json
        if os.path.exists('eval_report.json'):
            with open('eval_report.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                results = data.get('results', [])
                for item in results:
                    filename = item.get('file')
                    pred = item.get('predicted', {})
                    
                    src_path = os.path.join(receipts_dir, filename)
                    dest_path = os.path.join(uploads_dir, filename)
                    
                    if os.path.exists(src_path):
                        shutil.copy(src_path, dest_path)
                    
                    commerce = pred.get('Comercio')
                    if commerce == '---':
                        commerce = 'Desconocido'
                    
                    currency = pred.get('Moneda')
                    total = pred.get('Total')
                    
                    if currency in ['$', 'No detectada']:
                        try:
                            import re
                            clean_total = float(re.sub(r'[^\d.]', '', total))
                            if clean_total >= 1000:
                                currency = 'COP'
                            else:
                                currency = 'USD'
                        except Exception:
                            if 'synth_col' in filename or any(w in commerce.lower() for w in ['tiendas', 'exito', 'carulla', 'ara', 'jumbo']):
                                currency = 'COP'
                            else:
                                currency = 'USD'
                    
                    # Create invoice
                    inv = Invoice(
                        user_id=demo_user.id,
                        commerce=commerce,
                        date=pred.get('Fecha'),
                        currency=currency,
                        tax=pred.get('Impuestos'),
                        total=total,
                        image_path=f'/static/uploads/{filename}'
                    )
                    db.session.add(inv)
            print("Cargadas facturas de eval_report.json.")
        
        # 2. For other files in receipts, if we want to show a lot of data, we can mock their entries
        # so they can see all 240 invoices with beautiful graphs!
        import random
        from datetime import datetime, timedelta
        
        all_files = os.listdir(receipts_dir)
        added_count = 0
        
        # Filter for files that aren't already added
        existing_filenames = {item.get('file') for item in data.get('results', [])} if 'data' in locals() else set()
        
        merchants = ["TIENDAS D1", "SUPERMERCADOS EXITO", "CARULLA VIVERO", "JUMBO CENCOSUD", "ALMACENES ARA", "Taco Bell", "El Gran Mar", "McDonald's", "Starbucks", "KFC"]
        
        for fname in all_files:
            if fname in existing_filenames:
                continue
            if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
                
            src_path = os.path.join(receipts_dir, fname)
            dest_path = os.path.join(uploads_dir, fname)
            
            # Copy file
            try:
                shutil.copy(src_path, dest_path)
            except Exception as e:
                print(f"Error copying {fname}: {e}")
                continue
                
            # Generate random but realistic mock data for visualization
            merchant = random.choice(merchants)
            days_ago = random.randint(1, 60)
            date_str = (datetime.now() - timedelta(days=days_ago)).strftime('%d/%m/%Y')
            
            total_val = round(random.uniform(5000, 150000), 2)
            tax_val = round(total_val * 0.19, 2)
            
            currency_val = "COP" if total_val >= 1000 else "USD"
            
            inv = Invoice(
                user_id=demo_user.id,
                commerce=merchant,
                date=date_str,
                currency=currency_val,
                tax=str(tax_val),
                total=str(total_val),
                image_path=f'/static/uploads/{fname}'
            )
            db.session.add(inv)
            added_count += 1
            if added_count >= 80: # Load 80 more invoices to make the dashboard look populated but not too heavy
                break
                
        db.session.commit()
        print(f"Pobladas {added_count} facturas mockeadas adicionales.")

if __name__ == '__main__':
    populate()
