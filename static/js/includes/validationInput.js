document.getElementById("attachment").addEventListener("change", function () {
    const allowed = /\.(jpg|jpeg|png|pdf|doc|docx)$/i;
    let invalidFiles = [];

    [...this.files].forEach(file => {
        if (!allowed.test(file.name)) {
            invalidFiles.push(file.name);
        }
    });

    if (invalidFiles.length > 0) {
        // Masukkan pesan ke dalam modal
        document.getElementById("fileErrorBody").innerHTML =
            "<p>Gagal memilih file bukti, file anda:</p><ul>" +
            invalidFiles.map(f => `<li>${f}</li>`).join("") +
            "</ul><p>File yang dapat dikirim untuk saat ini: <strong>JPG, PNG, PDF, DOC, DOCX</strong> </p>";

        // Reset input
        this.value = "";

        // Tampilkan modal
        const errorModal = new bootstrap.Modal(document.getElementById("fileErrorModal"));
        errorModal.show();
    }
});