function initMap() {
    // Coordenadas padrão (exemplo: centro de uma cidade ou faculdade)
    const faculdade = { lat: -23.550520, lng: -46.633308 };
    
    const map = new google.maps.Map(document.getElementById("map"), {
        zoom: 14,
        center: faculdade,
    });

    new google.maps.Marker({
        position: faculdade,
        map: map,
        title: "Campus Universitário",
    });

    // Configuração do Google Places API no input
    const input = document.getElementById("autocomplete");
    const autocomplete = new google.maps.places.Autocomplete(input);
    autocomplete.bindTo("bounds", map);
}