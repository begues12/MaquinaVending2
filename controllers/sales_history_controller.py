"""
Controlador para el historial de ventas y exportación de datos - VERSION CORREGIDA
"""
import os
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import psutil
from database import db_manager

logger = logging.getLogger(__name__)

class SalesHistoryController:
    """Controlador para gestionar el historial de ventas y exportaciones"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_sales_history(self, 
                         start_date: Optional[str] = None, 
                         end_date: Optional[str] = None,
                         limit: int = 100) -> List[Dict]:
        """
        Obtener historial de ventas filtrado por fechas
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                s.id,
                s.created_at as timestamp,
                s.door_id,
                s.amount,
                s.payment_method,
                s.payment_id as transaction_id,
                s.status,
                p.name as product_name,
                s.amount as product_price,
                p.description as category
            FROM sales s
            LEFT JOIN products p ON s.door_id = p.door_id
            WHERE 1=1
            """
            
            params = []
            
            if start_date:
                query += " AND DATE(s.created_at) >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND DATE(s.created_at) <= ?"
                params.append(end_date)
                
            query += " ORDER BY s.created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.close()
            
            sales = []
            for row in result:
                sale = {
                    'id': row[0],
                    'timestamp': row[1],
                    'door_id': row[2],
                    'amount': row[3],
                    'payment_method': row[4],
                    'transaction_id': row[5] or 'N/A',
                    'status': row[6],
                    'product_name': row[7] or f'Producto Puerta {row[2]}',
                    'product_price': row[8] or 0.0,
                    'category': row[9] or 'Sin categoría'
                }
                sales.append(sale)
                
            self.logger.info(f"Obtenidas {len(sales)} ventas del historial")
            return sales
            
        except Exception as e:
            self.logger.error(f"Error al obtener historial de ventas: {e}")
            return []
    
    def get_sales_summary(self, 
                         start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> Dict:
        """
        Obtener resumen de ventas
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Consulta para totales
            query_totals = """
            SELECT 
                COUNT(*) as total_sales,
                SUM(amount) as total_revenue,
                AVG(amount) as avg_sale
            FROM sales 
            WHERE 1=1
            """
            
            params = []
            
            if start_date:
                query_totals += " AND DATE(created_at) >= ?"
                params.append(start_date)
                
            if end_date:
                query_totals += " AND DATE(created_at) <= ?"
                params.append(end_date)
            
            cursor.execute(query_totals, params)
            totals = cursor.fetchall()
            
            # Consulta para ventas por método de pago
            query_methods = """
            SELECT 
                payment_method,
                COUNT(*) as count,
                SUM(amount) as total
            FROM sales 
            WHERE 1=1
            """
            
            if start_date or end_date:
                if start_date:
                    query_methods += " AND DATE(created_at) >= ?"
                if end_date:
                    query_methods += " AND DATE(created_at) <= ?"
                    
            query_methods += " GROUP BY payment_method"
            
            cursor.execute(query_methods, params)
            methods = cursor.fetchall()
            
            # Consulta para productos más vendidos
            query_products = """
            SELECT 
                s.door_id,
                p.name,
                COUNT(*) as sales_count,
                SUM(s.amount) as total_revenue
            FROM sales s
            LEFT JOIN products p ON s.door_id = p.door_id
            WHERE 1=1
            """
            
            if start_date or end_date:
                if start_date:
                    query_products += " AND DATE(s.created_at) >= ?"
                if end_date:
                    query_products += " AND DATE(s.created_at) <= ?"
                    
            query_products += " GROUP BY s.door_id ORDER BY sales_count DESC LIMIT 10"
            
            cursor.execute(query_products, params)
            products = cursor.fetchall()
            
            conn.close()
            
            # Construir resumen
            summary = {
                'total_sales': totals[0][0] if totals else 0,
                'total_revenue': float(totals[0][1]) if totals and totals[0][1] else 0.0,
                'average_sale': float(totals[0][2]) if totals and totals[0][2] else 0.0,
                'payment_methods': [],
                'top_products': [],
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
            # Procesar métodos de pago
            for method in methods:
                summary['payment_methods'].append({
                    'method': method[0],
                    'count': method[1],
                    'total': float(method[2])
                })
            
            # Procesar productos más vendidos
            for product in products:
                summary['top_products'].append({
                    'door_id': product[0],
                    'product_name': product[1] or f'Puerta {product[0]}',
                    'sales_count': product[2],
                    'total_revenue': float(product[3])
                })
                
            return summary
            
        except Exception as e:
            self.logger.error(f"Error al obtener resumen de ventas: {e}")
            return {
                'total_sales': 0,
                'total_revenue': 0.0,
                'average_sale': 0.0,
                'payment_methods': [],
                'top_products': [],
                'period': {'start_date': start_date, 'end_date': end_date}
            }
    
    def export_sales_to_csv(self, 
                           start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> str:
        """
        Exportar ventas a archivo CSV
        """
        try:
            # Obtener datos de ventas
            sales = self.get_sales_history(start_date, end_date, limit=10000)
            
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"historial_ventas_{timestamp}.csv"
            filepath = os.path.join("exports", filename)
            
            # Crear directorio si no existe
            os.makedirs("exports", exist_ok=True)
            
            # Escribir archivo CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Fecha', 'Hora', 'Puerta', 'Producto', 
                    'Precio', 'Método Pago', 'ID Transacción', 'Estado'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for sale in sales:
                    # Parsear fecha y hora
                    dt = datetime.fromisoformat(sale['timestamp'].replace('Z', ''))
                    
                    writer.writerow({
                        'ID': sale['id'],
                        'Fecha': dt.strftime('%Y-%m-%d'),
                        'Hora': dt.strftime('%H:%M:%S'),
                        'Puerta': sale['door_id'],
                        'Producto': sale['product_name'],
                        'Precio': f"€{sale['amount']:.2f}",
                        'Método Pago': sale['payment_method'],
                        'ID Transacción': sale['transaction_id'],
                        'Estado': sale['status']
                    })
            
            self.logger.info(f"Archivo CSV exportado: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error al exportar CSV: {e}")
            raise
    
    def export_summary_to_json(self, 
                              start_date: Optional[str] = None, 
                              end_date: Optional[str] = None) -> str:
        """
        Exportar resumen de ventas a JSON
        """
        try:
            # Obtener resumen
            summary = self.get_sales_summary(start_date, end_date)
            
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resumen_ventas_{timestamp}.json"
            filepath = os.path.join("exports", filename)
            
            # Crear directorio si no existe
            os.makedirs("exports", exist_ok=True)
            
            # Escribir archivo JSON
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(summary, jsonfile, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Archivo JSON exportado: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error al exportar JSON: {e}")
            raise
    
    def detect_usb_drives(self) -> List[str]:
        """
        Detectar unidades USB conectadas
        """
        try:
            usb_drives = []
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                # En Windows, buscar unidades removibles
                if 'removable' in partition.opts or partition.fstype in ['FAT32', 'exFAT', 'NTFS']:
                    try:
                        # Verificar que la unidad esté accesible
                        usage = psutil.disk_usage(partition.mountpoint)
                        if usage.total > 0:
                            usb_drives.append(partition.mountpoint)
                    except:
                        continue
            
            # Filtrar unidades del sistema (en Windows)
            system_drives = ['C:\\']  # Ajustar según necesidad
            usb_drives = [drive for drive in usb_drives if drive not in system_drives]
            
            self.logger.info(f"Detectadas {len(usb_drives)} unidades USB: {usb_drives}")
            return usb_drives
            
        except Exception as e:
            self.logger.error(f"Error al detectar unidades USB: {e}")
            return []
    
    def auto_export_to_usb(self, 
                          start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> Dict:
        """
        Exportar automáticamente a USB si está conectado
        """
        try:
            usb_drives = self.detect_usb_drives()
            
            if not usb_drives:
                return {
                    'success': False,
                    'message': 'No se detectaron unidades USB',
                    'files': []
                }
            
            # Usar la primera unidad USB detectada
            usb_path = usb_drives[0]
            
            # Exportar archivos localmente primero
            csv_file = self.export_sales_to_csv(start_date, end_date)
            json_file = self.export_summary_to_json(start_date, end_date)
            
            # Crear carpeta en USB
            usb_folder = os.path.join(usb_path, "HistorialVentas")
            os.makedirs(usb_folder, exist_ok=True)
            
            # Copiar archivos a USB
            import shutil
            
            csv_usb_path = os.path.join(usb_folder, os.path.basename(csv_file))
            json_usb_path = os.path.join(usb_folder, os.path.basename(json_file))
            
            shutil.copy2(csv_file, csv_usb_path)
            shutil.copy2(json_file, json_usb_path)
            
            self.logger.info(f"Archivos exportados a USB: {usb_folder}")
            
            return {
                'success': True,
                'message': f'Archivos exportados exitosamente a {usb_path}',
                'files': [csv_usb_path, json_usb_path],
                'usb_path': usb_path
            }
            
        except Exception as e:
            self.logger.error(f"Error en exportación automática a USB: {e}")
            return {
                'success': False,
                'message': f'Error al exportar a USB: {str(e)}',
                'files': []
            }

# Instancia global del controlador
sales_history_controller = SalesHistoryController()
