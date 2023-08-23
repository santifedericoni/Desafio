# Backend para Dashboard de Negocios
API construida con Flask y conectada a MongoDB para gestionar y mostrar datos para un dashboard de negocios.
## Requisitos
- Python 3.7 o superior
## Instalación y ejecución
1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/santifedericoni/Desafio.git
   cd Desafio
2. **Crear un entorno virtual y activarlo**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # En Windows
   source venv/bin/activate  # En UNIX o MacOS
3. **Instalar las dependencias**:
   ```bash
   pip install -r requirements.txt
4. **Ejecutar la aplicación**:
   ```bash
   python app.py
## Rutas
### Resumen del mes
- **URL:** `/summary/<month_year>`
- **Método:** `GET`
- **Ejemplo:** `/summary/05-2023`
- **Descripción:** Obtiene un resumen del mes con información de socios y variaciones.
### Datos del mes
- **URL:** `/charges/<month_year>`
- **Método:** `GET`
- **Ejemplo:** `/charges/05-2023`
- **Descripción:** Obtiene los cobros de cada día del mes, separados por Altas y Recurrencias.
### Total de valores del mes
- **URL:** `/total-values/<business>/<month_year>`
- **Método:** `GET`
- **Descripción:** Obtiene el valor total cobrado por un negocio y sus variaciones respecto al mes anterior.
### Gráficos de torta
- **URL:** `/pie-chart/<month_year>`
- **Método:** `GET`
- **Descripción:** Obtiene los porcentajes de dinero cobrado por tipo de cobro y nivel de acceso.
## Autor
Santiago Federiconi
