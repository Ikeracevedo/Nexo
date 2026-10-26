# 12 · Preguntas frecuentes

## Sobre los permisos

**¿Nexo puede ver los datos de otros empleados?**
No. Cada respuesta se construye con el token de quien pregunta, y ese token solo abre lo que esa persona ya puede abrir. No existe ninguna ruta en el código donde Nexo consulte datos de un usuario usando el token de otro, y hay un test automático que lo fija.

**¿Por qué pide `Group.Read.All`, que suena a mucho?**
Es un requisito de la API de Planner: los planes viven dentro de grupos de Microsoft 365, así que para resolverlos hay que poder leer a qué grupos pertenece la persona. Lee **la pertenencia**, no el contenido de los grupos. Es el único permiso de la lista que exige consentimiento de administrador.

**¿Puede escribir o borrar algo en Microsoft 365?**
No. Todos los permisos son de lectura. Nexo no puede crear eventos, completar tareas ni enviar mensajes en tu nombre.

**¿Y si un usuario no quiere que lea sus chats?**
Es lo que pasa por defecto: la lectura de conversaciones está apagada hasta que esa persona escribe `vigilar`, y se apaga con `no vigilar`.

## Sobre los datos

**¿Se guardan nuestras conversaciones?**
No. El texto se procesa en memoria para detectar compromisos y se descarta. Lo que queda guardado es el pendiente que redactó el modelo y el enlace al mensaje original, que sigue viviendo en Teams.

**¿Dónde están físicamente los datos?**
En el clúster de MongoDB Atlas que **tu empresa** crea, en la región que **tu empresa** elige. Nosotros no tenemos acceso.

**¿Nexo entrena modelos con nuestros datos?**
La aplicación no entrena ningún modelo. Lo que haga Google con el texto que recibe se rige por las condiciones de uso de Gemini, que hay que revisar antes de aprobar su uso con información sensible.

## Sobre el funcionamiento

**¿Funciona en el móvil?**
Sí. Nexo vive dentro de Teams, así que funciona en Teams de escritorio, web y móvil sin nada adicional.

**¿Qué pasa si se cae una fuente?**
Las demás siguen funcionando y Nexo **avisa de cuál no pudo consultar**. Un fallo nunca se traduce en una lista vacía: eso sería mentir por omisión.

**¿Y si Gemini no responde o se agota la cuota?**
`semana`, `recuérdame` y las tarjetas siguen funcionando igual. Solo se degradan las respuestas en lenguaje natural y `revisar`, con un mensaje honesto.

**Planner me sale vacío.**
Casi siempre no es un fallo: Planner solo devuelve tareas si perteneces a grupos de Microsoft 365 con planes creados. Crea un plan de prueba en `tasks.office.com` y vuelve a intentarlo.

**¿Cuántos usuarios aguanta?**
El cuello de botella es la cuota de Microsoft Graph y el plan de Atlas, no la aplicación. Para un piloto de decenas de usuarios, la capa gratuita de Atlas (M0, 512 MB) es suficiente.

## Sobre la instalación

**¿Cuánto cuesta mantenerlo?**
Desde unos 15 USD al mes: la VM es el único coste fijo. Entra ID, Azure Bot F0, Atlas M0 y la cuota gratuita de Gemini no cuestan nada en un piloto.

**¿Hace falta ser administrador global?**
Para crear el registro de aplicación y conceder el consentimiento, sí (o *Application Administrator*). Para el resto, no.

**Nuestro tenant no permite apps personalizadas en Teams.**
Entonces no se puede instalar hasta cambiar esa política en el centro de administración de Teams. **Compruébalo antes de empezar**: es el único requisito que puede bloquear el proyecto varios días.

**¿Se puede usar con varias empresas a la vez?**
Sí, si el registro se crea como multiinquilino (paso 3.1). Cada organización consiente por su cuenta. Ten en cuenta que, sin el distintivo *Verified Publisher* de Microsoft, en la pantalla de consentimiento aparecerá un aviso de editor no verificado, y en tenants con el consentimiento de usuario deshabilitado solo podrá aprobarlo un administrador.

**¿Podemos cambiarle el nombre?**
Sí: la variable `BOT_NOMBRE` cambia cómo se presenta el asistente en la ayuda, las tarjetas y los prompts. El nombre visible en Teams se cambia en el `manifest.json`.

## Sobre el soporte

**¿Quién mantiene esto?**
El software lo desarrolla y mantiene el equipo del proyecto. **La instalación, las credenciales y la infraestructura son de cada empresa**, que puede auditarlas y revocarlas sin depender de nadie externo.

**¿Dónde reporto un fallo?**
En las *Issues* del repositorio, con la salida de `docker compose logs app` del momento del error — **sin pegar el contenido del `.env`**.
