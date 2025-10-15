document.addEventListener('DOMContentLoaded', function () {
	const dropZone = document.getElementById('dropZone');
	const fileInput = document.getElementById('dateien');
	const dateiliste = document.getElementById('dateiListe');
	const thumbnailListe = document.getElementById('thumbnailListe');
	const uploadBtn = document.getElementById('upload');

	if (dropZone && fileInput) {
		// Drag & Drop Events
		dropZone.addEventListener('dragenter', handleDragEnter, false);
		dropZone.addEventListener('dragover', handleDragOver, false);
		dropZone.addEventListener('dragleave', handleDragLeave, false);
		dropZone.addEventListener('drop', handleDrop, false);

		fileInput.addEventListener('change', updateFileList, false);
	}

	function handleDragEnter(e) {
		e.preventDefault();
		dropZone.classList.add('dragover');
	}
	function handleDragOver(e) {
		e.preventDefault();
		dropZone.classList.add('dragover');
	}
	function handleDragLeave(e) {
		e.preventDefault();
		dropZone.classList.remove('dragover');
	}
	function handleDrop(e) {
		e.preventDefault();
		dropZone.classList.remove('dragover');
		const files = e.dataTransfer.files;
		fileInput.files = files;
		updateFileList();
	}

	function updateFileList() {
		dateiliste.innerHTML = '';
		thumbnailListe.innerHTML = '';
		const files = fileInput.files;
		if (!files || files.length === 0) return;
		for (const file of files) {
			const li = document.createElement('li');
			li.textContent = `${file.name} (${file.type || 'n/a'}) - ${file.size} bytes`;
			dateiliste.appendChild(li);
			if (file.type.startsWith('image/')) {
				const img = document.createElement('img');
				img.src = URL.createObjectURL(file);
				img.alt = file.name;
				img.onload = () => URL.revokeObjectURL(img.src);
				const thumbLi = document.createElement('li');
				thumbLi.appendChild(img);
				thumbnailListe.appendChild(thumbLi);
			}
		}
	}

	if (uploadBtn) {
		uploadBtn.addEventListener('click', function() {
			if (!fileInput.files || fileInput.files.length === 0) {
				alert('Bitte mindestens eine Datei auswählen.');
				return;
			}
			// Hier könnte ein Upload per AJAX implementiert werden
			alert('Upload-Button gedrückt. (Demo)');
		});
	}
});