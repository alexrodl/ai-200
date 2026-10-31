namespace Api;

/// <summary>Opiniones de clientes de ejemplo para generar carga en la cola desde la web.</summary>
public static class SampleTexts
{
    private static readonly string[] Texts =
    [
        "Pedí una notebook el lunes y llegó el miércoles, bien embalada y con todos los accesorios. " +
        "El equipo es rápido, la pantalla se ve excelente y la batería dura todo el día. La recomiendo sin dudas.",

        "La aplicación se cuelga cada vez que intento pagar con tarjeta. Escribí tres veces a soporte y nadie respondió. " +
        "Terminé comprando en otro sitio; la experiencia fue muy mala y no pienso volver.",

        "El curso cubre los temas prometidos: contenedores, revisiones y escalado. Algunas prácticas fueron largas, " +
        "pero el instructor explicó con claridad y los laboratorios funcionaron en Azure.",

        "Contraté el plan anual porque el precio era bueno, pero a los dos meses lo aumentaron sin avisar. " +
        "El servicio en sí funciona bien, aunque la falta de transparencia me molestó bastante.",

        "El restaurante tiene una terraza muy linda y la comida llegó caliente y a tiempo. " +
        "El postre fue lo mejor de la noche y el personal estuvo atento en todo momento. Volveremos pronto.",

        "La actualización nueva borró mis configuraciones y ahora la app tarda mucho en abrir. " +
        "Antes era la herramienta que más usaba; hoy busco una alternativa porque así no puedo trabajar.",

        "Hice la migración de la API a Azure Container Apps en una tarde. Con las identidades administradas no tuve que " +
        "guardar claves, y el escalado a cero redujo bastante el costo mensual del equipo.",

        "El hotel estaba bien ubicado y la habitación limpia, pero el wifi no funcionó durante toda la estadía " +
        "y el desayuno fue escaso. Por el precio que pagamos esperaba un poco más."
    ];

    public static string Pick(int index) => Texts[index % Texts.Length];
}
