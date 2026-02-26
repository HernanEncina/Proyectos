// editor.js

document.addEventListener('DOMContentLoaded', () => {
    // Seleccionamos los elementos editables
    const nameField = document.querySelector('.recipient-name');
    const reasonField = document.querySelector('.reason');

    // Hacemos que los campos sean editables al hacer clic
    nameField.setAttribute('contenteditable', 'true');
    reasonField.setAttribute('contenteditable', 'true');

    // Opcional: Limpiar el formato al pegar texto
    [nameField, reasonField].forEach(field => {
        field.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = e.clipboardData.getData('text/plain');
            document.execCommand('insertText', false, text);
        });
    });
});

// Función para imprimir el certificado
function imprimirCertificado() {
    window.print();
}