import os
import shutil
from app import app, db, smart_process
from models import User, Invoice

def populate_real():
    with app.app_context():
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            print("Error: Usuario 'demo' no encontrado.")
            return
            
        # Clean existing invoices first
        Invoice.query.filter_by(user_id=demo_user.id).delete()
        db.session.commit()
        print("[*] Base de datos limpia de facturas anteriores.")
        
        receipts_dir = 'receipts'
        uploads_dir = os.path.join('static', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Select 25 files to run actual OCR pipeline on.
        # We will prioritize the ones from the evaluation report, plus some others.
        target_files = []
        
        # Add the synthetic ones (usually high quality and fast to parse)
        synth_files = [f"synth_col_0{i}.jpg" for i in range(10)]
        target_files.extend(synth_files)
        
        # Add real receipts from 1000 to 1015
        for i in range(1000, 1016):
            target_files.append(f"{i}-receipt.jpg")
            
        print(f"[*] Total de facturas a procesar con EasyOCR real: {len(target_files)}")
        
        processed_count = 0
        for fname in target_files:
            src_path = os.path.join(receipts_dir, fname)
            if not os.path.exists(src_path):
                continue
                
            print(f"[{processed_count + 1}/{len(target_files)}] Procesando OCR para {fname}...", end="", flush=True)
            
            # Copy source file to uploads first so smart_process can save scanned images alongside it
            dest_path = os.path.join(uploads_dir, fname)
            shutil.copy(src_path, dest_path)
            
            try:
                # Run actual OCR pipeline
                result = smart_process(dest_path)
                if result:
                    parsed = result.get('parsed_info', {})
                    
                    # Apply currency disambiguation
                    currency = parsed.get('Moneda')
                    total = parsed.get('Total')
                    
                    if currency in ['$', 'No detectada']:
                        try:
                            import re
                            clean_total = float(re.sub(r'[^\d.]', '', total))
                            if clean_total >= 1000:
                                currency = 'COP'
                            else:
                                currency = 'USD'
                        except Exception:
                            if 'synth_col' in fname or any(w in parsed.get('Comercio', '').lower() for w in ['tiendas', 'exito', 'carulla', 'ara', 'jumbo']):
                                currency = 'COP'
                            else:
                                currency = 'USD'
                    
                    inv = Invoice(
                        user_id=demo_user.id,
                        commerce=parsed.get('Comercio', 'Desconocido'),
                        date=parsed.get('Fecha', '---'),
                        currency=currency,
                        tax=parsed.get('Impuestos', '---'),
                        total=total,
                        image_path=result['images']['scan'] # Use the cropped scanned image path!
                    )
                    db.session.add(inv)
                    processed_count += 1
                    print(" COMPLETO")
                else:
                    print(" FALLÓ (Procesamiento devolvió None)")
            except Exception as e:
                print(f" ERROR: {e}")
                
        db.session.commit()
        print(f"\n[*] Proceso finalizado. Se cargaron {processed_count} facturas reales a la base de datos.")

if __name__ == '__main__':
    populate_real()
