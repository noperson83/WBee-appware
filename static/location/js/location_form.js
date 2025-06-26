// JavaScript to dynamically populate Location form dropdowns
function updateChoices(catId) {
    const endpoints = {
        location_type: `/location/ajax/location-types/?business_category=${catId}`,
        status: `/location/ajax/dynamic-choices/?business_category=${catId}&choice_type=location_status`,
        access_requirements: `/location/ajax/dynamic-choices/?business_category=${catId}&choice_type=access_requirement`,
        work_hours: `/location/ajax/dynamic-choices/?business_category=${catId}&choice_type=work_hours`
    };

    for (const [field, url] of Object.entries(endpoints)) {
        fetch(url)
            .then(r => r.json())
            .then(data => {
                const select = document.getElementById(`id_${field}`);
                if (!select) return;
                select.innerHTML = '';
                const choices = data[field + 's'] || data.choices || [];
                choices.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id || c[0] || c.value;
                    opt.textContent = c.name || c[1] || c.display_name || c.text || c;
                    select.appendChild(opt);
                });
            });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const bc = document.getElementById('id_business_category');
    if (!bc) return;
    bc.addEventListener('change', e => {
        const val = e.target.value;
        if (val) updateChoices(val);
    });
    if (bc.value) updateChoices(bc.value);
});
