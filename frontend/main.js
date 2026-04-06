document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('table-body');
    const emptyState = document.getElementById('empty-state');
    const refreshBtn = document.getElementById('refresh-btn');
    const searchInput = document.getElementById('search-input');
    
    const totalCountEl = document.getElementById('total-count');


    let certificatesData = [];

    async function loadData() {
        try {
            // Usa query param t para não fazer cache
            const response = await fetch(`public/dados_extraidos.json?t=${new Date().getTime()}`);
            if (!response.ok) return [];
            return await response.json();
        } catch (error) {
            console.error('Erro ao carregar dados:', error);
            return [];
        }
    }

    function renderTable(data) {
        tableBody.innerHTML = '';
        
        totalCountEl.textContent = data.length;

        if (data.length === 0) {
            emptyState.style.display = 'block';
            tableBody.closest('.table-wrapper').style.display = 'none';
        } else {
            emptyState.style.display = 'none';
            tableBody.closest('.table-wrapper').style.display = 'block';

            data.forEach((item, index) => {
                const tr = document.createElement('tr');
                tr.style.animation = `fadeInUp 0.3s ease-out ${index * 0.05}s both`;
                
                tr.innerHTML = `
                    <td class="patient-name">${item.nome_paciente || 'N/A'}</td>
                    <td>${item.nome_medico || 'N/A'}</td>
                    <td>${item.crm || 'N/A'}</td>
                    <td class="text-center">${item.validacao_profissional?.crm_formato_valido ? '<span class="crm-valid" title="Formato OK">✅</span>' : '<span class="crm-invalid" title="' + (item.validacao_profissional?.conclusao_tecnica || 'Inválido') + '">❌</span>'}</td>
                    <td>${formatDate(item.data_atendimento)}</td>

                    <td><span class="badge ${item.cid ? 'badge-cid' : ''}">${item.cid || 'N/A'}</span></td>
                    <td class="text-center font-weight-bold">${item.dias_afastamento ? item.dias_afastamento + (typeof item.dias_afastamento === 'number' ? ' dias' : '') : 'N/A'}</td>
                    <td><span class="badge badge-status status-${(item.auditoria?.status || 'pendente').toLowerCase()}" title="${(item.auditoria?.alertas || []).join(', ')}">${item.auditoria?.status || 'Pendente'}</span></td>
                    <td><span class="file-tag" title="${item.arquivo_origem}">${item.arquivo_origem || '-'}</span></td>
                `;
                
                tableBody.appendChild(tr);
            });
        }
    }

    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const parts = dateString.split('-');
        if(parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        return dateString;
    }

    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                obj.innerHTML = end;
            }
        };
        window.requestAnimationFrame(step);
    }

    async function refreshDashboard() {
        const icon = refreshBtn.querySelector('.feather-refresh-ccw');
        icon.classList.add('spin-anim');
        
        certificatesData = await loadData();
        renderTable(certificatesData);
        
        setTimeout(() => {
            icon.classList.remove('spin-anim');
        }, 600);
    }

    refreshDashboard();

    refreshBtn.addEventListener('click', refreshDashboard);
    
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filteredData = certificatesData.filter(item => {
            return (item.nome_paciente && item.nome_paciente.toLowerCase().includes(query)) ||
                   (item.crm && item.crm.toLowerCase().includes(query)) ||
                   (item.nome_medico && item.nome_medico.toLowerCase().includes(query)) ||
                   (item.cid && item.cid.toLowerCase().includes(query));
        });
        renderTable(filteredData);
    });
});
