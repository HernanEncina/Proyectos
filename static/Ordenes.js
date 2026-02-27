// static/ordenes.js
// Sistema de órdenes y pagos para TecSalud

// ============================================
// CONFIGURACIÓN
// ============================================
const API_BASE = ''; // Si está en el mismo dominio, vacío. Si no: 'http://tu-servidor:7070'

// ============================================
// UTILIDADES
// ============================================

/**
 * Formatea un número a precio mexicano
 * @param {number} precio - El precio a formatear
 * @returns {string} Precio formateado (ej: $1,500.00)
 */
function formatearPrecio(precio) {
    return precio.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

/**
 * Muestra un mensaje de error en el elemento especificado
 * @param {string} mensaje - Mensaje de error
 * @param {string} elementoId - ID del elemento donde mostrar el error
 */
function mostrarError(mensaje, elementoId = 'error-mensaje') {
    const errorDiv = document.getElementById(elementoId);
    if (errorDiv) {
        errorDiv.textContent = mensaje;
        errorDiv.style.display = 'block';
        
        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    } else {
        alert(mensaje);
    }
}

/**
 * Oculta el mensaje de error
 * @param {string} elementoId - ID del elemento de error
 */
function ocultarError(elementoId = 'error-mensaje') {
    const errorDiv = document.getElementById(elementoId);
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

/**
 * Muestra un modal de éxito
 * @param {Object} datos - Datos de la donación exitosa
 */
function mostrarExito(datos) {
    const { donacionId, folio, email } = datos;
    
    console.log('Mostrando modal de éxito para:', email); // DEBUG
    
    // Crear modal de éxito
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    `;
    
    // IMPORTANTE: Las comillas están CORREGIDAS aquí
    modal.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 10px; max-width: 400px; text-align: center;">
            <h2 style="color: #27ae60;">✅ ¡Gracias por tu donación!</h2>
            <p>Tu certificado se ha descargado automáticamente.</p>
            <p><strong>Folio:</strong> ${folio || 'N/A'}</p>
            <p><strong>ID de donación:</strong> ${donacionId || 'N/A'}</p>
            <p><small>Puedes volver a descargar tu certificado desde la sección "Mis certificados"</small></p>
            <div style="margin-top: 20px;">
                <button onclick="window.location.href='/orden'" 
                    style="background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px;">
                    Nueva Donación
                </button>
                <button onclick="window.location.href='/mis-certificados?email=${encodeURIComponent(email)}'" 
                    style="background: #2ecc71; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px;">
                    Ver Mis Certificados
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Cerrar al hacer clic fuera
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// ============================================
// FUNCIONES PARA RESUMEN_COMPRA.HTML
// ============================================

const Ordenes = {
    /**
     * Estado de la orden actual
     */
    estado: {
        certificados: [],
        certificadoSeleccionado: null,
        donacionTemp: null
    },

    /**
     * Inicializa la página de resumen de compra
     */
    initResumen: function() {
        this.cargarCertificados();
        
        // Event listeners
        const tipoCert = document.getElementById('tipo-certificado');
        const cantidad = document.getElementById('cantidad');
        const beneficiario = document.getElementById('beneficiario');
        const mensaje = document.getElementById('mensaje');
        const donarBtn = document.getElementById('donar-btn');
        
        if (tipoCert) tipoCert.addEventListener('change', () => this.actualizarResumen());
        if (cantidad) cantidad.addEventListener('input', () => this.actualizarResumen());
        if (beneficiario) beneficiario.addEventListener('input', () => this.actualizarResumen());
        if (mensaje) mensaje.addEventListener('input', () => this.actualizarResumen());
        if (donarBtn) donarBtn.addEventListener('click', () => this.procesarDonacion());
    },

    /**
     * Carga los certificados desde la API
     */
    cargarCertificados: async function() {
        try {
            const response = await fetch(`${API_BASE}/api/certificados`);
            const data = await response.json();
            
            if (data.certificados && data.certificados.length > 0) {
                this.estado.certificados = data.certificados;
                
                const select = document.getElementById('tipo-certificado');
                if (!select) return;
                
                select.innerHTML = '<option value="">Selecciona un certificado</option>';
                
                this.estado.certificados.forEach(cert => {
                    const option = document.createElement('option');
                    option.value = cert.id;
                    option.textContent = `${cert.nombre} - $${formatearPrecio(cert.precio)}`;
                    option.dataset.precio = cert.precio;
                    option.dataset.nombre = cert.nombre;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error cargando certificados:', error);
            const select = document.getElementById('tipo-certificado');
            if (select) {
                select.innerHTML = '<option value="">Error cargando certificados</option>';
            }
        }
    },

    /**
     * Actualiza el resumen de la orden
     */
    actualizarResumen: function() {
        const select = document.getElementById('tipo-certificado');
        const cantidad = parseInt(document.getElementById('cantidad')?.value) || 1;
        const beneficiario = document.getElementById('beneficiario')?.value.trim() || '';
        const mensaje = document.getElementById('mensaje')?.value.trim() || '';
        
        if (!select) return;
        
        const selectedOption = select.options[select.selectedIndex];
        
        if (select.value && selectedOption.dataset) {
            const nombre = selectedOption.dataset.nombre;
            const precio = parseFloat(selectedOption.dataset.precio);
            const total = precio * cantidad;
            
            this.estado.certificadoSeleccionado = {
                id: parseInt(select.value),
                nombre: nombre,
                precio: precio,
                cantidad: cantidad,
                beneficiario: beneficiario || null,
                mensaje: mensaje || null
            };
            
            // Actualizar elementos del DOM
            const resumenItem = document.getElementById('resumen-item');
            const resumenTotal = document.getElementById('resumen-total');
            
            if (resumenItem) {
                resumenItem.innerHTML = `${nombre} x${cantidad}<br><small>$${formatearPrecio(precio)} c/u</small>`;
            }
            
            if (resumenTotal) {
                resumenTotal.innerHTML = `
                    <span>Total:</span>
                    <span>$${formatearPrecio(total)}</span>
                `;
            }
        } else {
            this.estado.certificadoSeleccionado = null;
            
            const resumenItem = document.getElementById('resumen-item');
            const resumenTotal = document.getElementById('resumen-total');
            
            if (resumenItem) resumenItem.innerHTML = 'Certificado: -';
            if (resumenTotal) {
                resumenTotal.innerHTML = `
                    <span>Total:</span>
                    <span>$0</span>
                `;
            }
        }
    },

    /**
 * Procesa la donación y redirige a pago
 */
procesarDonacion: function() {
    if (!this.estado.certificadoSeleccionado) {
        alert('Selecciona un certificado');
        return;
    }
    
    const nombreTitular = document.getElementById('nombre_titular_compra')?.value.trim();
    const email = document.getElementById('email')?.value.trim();
    
    if (!nombreTitular) {
        alert('Ingresa el nombre del donante (titular)');
        return;
    }
    
    if (!email) {
        alert('Ingresa tu correo');
        return;
    }
    
    // Validar email
    if (!email.includes('@') || !email.includes('.')) {
        alert('Ingresa un correo válido');
        return;
    }
    
    const donacionData = {
        nombre_titular: nombreTitular,  // ← Quién DONA (titular de la tarjeta)
        email: email,
        items: [{
            certificado_id: this.estado.certificadoSeleccionado.id,
            nombre: this.estado.certificadoSeleccionado.nombre,
            cantidad: this.estado.certificadoSeleccionado.cantidad,
            precio: this.estado.certificadoSeleccionado.precio,
            nombre_beneficiario: this.estado.certificadoSeleccionado.beneficiario || nombreTitular,  // ← A nombre de quién (si no se especifica, es el titular)
            mensaje: this.estado.certificadoSeleccionado.mensaje
        }]
    };
    
    // Guardar en sessionStorage para la página de pago
    sessionStorage.setItem('donacion_temp', JSON.stringify(donacionData));
    
    // Redirigir a página de pago
    window.location.href = '/pago';
},

    // ============================================
    // FUNCIONES PARA PAGO.HTML
    // ============================================

    /**
     * Inicializa la página de pago
     */
    initPago: function() {
        // Recuperar datos de sessionStorage
        const stored = sessionStorage.getItem('donacion_temp');
        if (!stored) {
            alert('No hay información de donación. Por favor, selecciona un certificado primero.');
            window.location.href = 'Resumen_compra.html';
            return;
        }
        
        try {
            this.estado.donacionTemp = JSON.parse(stored);
            this.mostrarResumenPago();
        } catch (e) {
            alert('Error cargando datos de donación');
            window.location.href = 'Resumen_compra.html';
        }
        
        // Event listeners
        const procesarBtn = document.getElementById('procesar-pago-btn');
        if (procesarBtn) {
            procesarBtn.addEventListener('click', () => this.procesarPago());
        }
        
        // Formatear campos de tarjeta
        const numTarj = document.getElementById('num_tarj');
        const fechaExp = document.getElementById('fecha_exp');
        const cvv = document.getElementById('cvv');
        
        if (numTarj) {
            numTarj.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 0) {
                    value = value.match(new RegExp('.{1,4}', 'g')).join(' ');
                }
                e.target.value = value;
            });
        }
        
        if (fechaExp) {
            fechaExp.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length >= 2) {
                    value = value.substring(0,2) + '/' + value.substring(2,4);
                }
                e.target.value = value;
            });
        }
        
        if (cvv) {
            cvv.addEventListener('input', function(e) {
                e.target.value = e.target.value.replace(/\D/g, '');
            });
        }
    },

    /**
     * Muestra el resumen en la página de pago
     */
    mostrarResumenPago: function() {
        if (!this.estado.donacionTemp) return;
        
        const itemsContainer = document.getElementById('items-resumen');
        const totalContainer = document.getElementById('total-resumen');
        
        if (!itemsContainer || !totalContainer) return;
        
        let html = '';
        let total = 0;
        
        this.estado.donacionTemp.items.forEach(item => {
            const subtotal = item.precio * item.cantidad;
            total += subtotal;
            
            html += `
                <div class="item" style="margin-bottom: 10px;">
                    <div><strong>${item.nombre}</strong> x${item.cantidad}</div>
                    <div>$${formatearPrecio(subtotal)}</div>
                    ${item.nombre_beneficiario ? `<div><small>Beneficiario: ${item.nombre_beneficiario}</small></div>` : ''}
                </div>
            `;
        });
        
        itemsContainer.innerHTML = html;
        totalContainer.innerHTML = `
            <span>Total a pagar:</span>
            <span>$${formatearPrecio(total)}</span>
        `;
    },

    /**
     * Valida el formulario de pago
     * @returns {boolean} True si es válido
     */
    validarFormularioPago: function() {
        let valido = true;
        const campos = [
            { id: 'nombre_titular', mensaje: 'Ingresa el nombre del titular' },
            { id: 'email', mensaje: 'Ingresa tu correo' },
            { id: 'num_tarj', mensaje: 'Ingresa el número de tarjeta' },
            { id: 'cvv', mensaje: 'Ingresa el CVV' },
            { id: 'fecha_exp', mensaje: 'Ingresa la fecha de expiración' }
        ];
        
        // Remover errores previos
        document.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
        
        for (const campo of campos) {
            const input = document.getElementById(campo.id);
            if (!input) continue;
            
            const valor = input.value.trim();
            
            if (!valor) {
                input.classList.add('error');
                mostrarError(campo.mensaje);
                valido = false;
                break;
            }
            
            // Validaciones específicas
            if (campo.id === 'email') {
                if (!valor.includes('@') || !valor.includes('.')) {
                    input.classList.add('error');
                    mostrarError('Ingresa un correo válido');
                    valido = false;
                    break;
                }
            }
            
            if (campo.id === 'num_tarj') {
                const numeros = valor.replace(/\s/g, '');
                if (numeros.length < 15 || numeros.length > 16) {
                    input.classList.add('error');
                    mostrarError('Número de tarjeta inválido');
                    valido = false;
                    break;
                }
            }
            
            if (campo.id === 'cvv') {
                if (valor.length < 3 || valor.length > 4) {
                    input.classList.add('error');
                    mostrarError('CVV inválido');
                    valido = false;
                    break;
                }
            }
            
            if (campo.id === 'fecha_exp') {
                if (!valor.match(/^\d{2}\/\d{2}$/)) {
                    input.classList.add('error');
                    mostrarError('Formato de fecha inválido (MM/AA)');
                    valido = false;
                    break;
                }
                
                // Validar que no sea fecha pasada
                const [mes, año] = valor.split('/');
                const fechaExp = new Date(2000 + parseInt(año), parseInt(mes) - 1);
                const hoy = new Date();
                
                if (fechaExp < hoy) {
                    input.classList.add('error');
                    mostrarError('La tarjeta está vencida');
                    valido = false;
                    break;
                }
            }
        }
        
        return valido;
    },

    /**
     * Procesa el pago y descarga el certificado
     */
    procesarPago: async function() {
        // Validar formulario
        if (!this.validarFormularioPago()) {
            return;
        }
        
        // Mostrar loading
        const procesarBtn = document.getElementById('procesar-pago-btn');
        const loadingDiv = document.getElementById('loading');
        
        if (procesarBtn) procesarBtn.disabled = true;
        if (loadingDiv) loadingDiv.style.display = 'block';
        
        ocultarError();
        
        // Preparar datos finales
        const datosPago = {
            nombre_titular: document.getElementById('nombre_titular')?.value.trim() || '',
            email: document.getElementById('email')?.value.trim() || '',
            items: this.estado.donacionTemp?.items || []
        };
        
        try {
            const response = await fetch(`${API_BASE}/api/procesar-pago`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(datosPago)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error al procesar el pago');
            }
            
            // Obtener headers
            const donacionId = response.headers.get('X-Donacion-ID');
            const folio = response.headers.get('X-Folio');
            
            // Verificar si es una imagen (certificado)
            const contentType = response.headers.get('Content-Type');
            
            if (contentType && contentType.includes('image/png')) {
                // Descargar el certificado
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `certificado_${folio || 'donacion'}.png`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                
                // Limpiar sessionStorage
                sessionStorage.removeItem('donacion_temp');
                
                // Mostrar mensaje de éxito
                mostrarExito({
                    donacionId: donacionId,
                    folio: folio,
                    email: datosPago.email
                });
            } else {
                // Si no es imagen, algo salió mal
                const data = await response.json();
                throw new Error(data.message || 'Respuesta inesperada del servidor');
            }
            
        } catch (error) {
            mostrarError(error.message);
            if (procesarBtn) procesarBtn.disabled = false;
            if (loadingDiv) loadingDiv.style.display = 'none';
        }
    },

    // ============================================
    // FUNCIONES PARA MIS-CERTIFICADOS.HTML
    // ============================================

    /**
     * Inicializa la página de mis certificados
     */
    initMisCertificados: function() {
        const urlParams = new URLSearchParams(window.location.search);
        const email = urlParams.get('email');
        
        const container = document.getElementById('certificados-container');
        if (!container) return;
        
        if (!email) {
            // Si no hay email, pedirlo
            container.innerHTML = `
                <div style="text-align: center; padding: 50px;">
                    <h2>Ingresa tu email</h2>
                    <input type="email" id="email-input" placeholder="tu@email.com" 
                        style="padding: 10px; width: 300px; margin-bottom: 10px;">
                    <button onclick="Ordenes.buscarPorEmail()" 
                        style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        Buscar
                    </button>
                </div>
            `;
        } else {
            this.cargarCertificadosUsuario(email);
        }
    },

    /**
     * Busca certificados por email desde el input
     */
    buscarPorEmail: function() {
        const emailInput = document.getElementById('email-input');
        if (emailInput && emailInput.value) {
            window.location.href = `mis-certificados.html?email=${encodeURIComponent(emailInput.value)}`;
        }
    },

    /**
     * Carga los certificados de un usuario
     * @param {string} email - Email del usuario
     */
    cargarCertificadosUsuario: async function(email) {
        try {
            const response = await fetch(`${API_BASE}/api/mis-certificados/${encodeURIComponent(email)}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            const container = document.getElementById('certificados-container');
            if (!container) return;
            
            if (!data.certificados || data.certificados.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 50px;">
                        <h2>No se encontraron certificados</h2>
                        <p>Para el email: ${email}</p>
                        <a href="Resumen_compra.html" 
                            style="display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                            Hacer una donación
                        </a>
                    </div>
                `;
                return;
            }
            
            let html = `<h2>Certificados encontrados: ${data.total_certificados}</h2>`;
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;">';
            
            data.certificados.forEach(cert => {
                html += `
                    <div style="background: #f8f9fa; border-radius: 10px; padding: 20px; border: 1px solid #dee2e6;">
                        <h3 style="margin-top: 0;">${cert.certificado_nombre}</h3>
                        <p><strong>Beneficiario:</strong> ${cert.nombre_beneficiario}</p>
                        <p><strong>Cantidad:</strong> ${cert.cantidad}</p>
                        <p><strong>Monto:</strong> $${formatearPrecio(cert.monto_total)}</p>
                        <p><strong>Folio:</strong> ${cert.folio}</p>
                        <p><small>${new Date(cert.fecha).toLocaleDateString()}</small></p>
                        <p><small>Descargado: ${cert.veces_descargado} veces</small></p>
                        <div style="display: flex; gap: 10px; margin-top: 15px;">
                            <a href="${cert.url_ver}" target="_blank" 
                                style="flex: 1; background: #3498db; color: white; padding: 8px; text-align: center; text-decoration: none; border-radius: 5px;">
                                Ver
                            </a>
                            <a href="${cert.url_descargar}" 
                                style="flex: 1; background: #27ae60; color: white; padding: 8px; text-align: center; text-decoration: none; border-radius: 5px;">
                                Descargar
                            </a>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
            
        } catch (error) {
            const container = document.getElementById('certificados-container');
            if (container) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 50px; color: red;">
                        <h2>Error</h2>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
    }
};

// ============================================
// EXPORTAR PARA USO GLOBAL
// ============================================
window.Ordenes = Ordenes;