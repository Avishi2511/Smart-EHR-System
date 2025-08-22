import { NFC } from 'nfc-pcsc';

export const writeToCard = async (formData) => {
    return new Promise((resolve, reject) => {
        const nfc = new NFC();

        nfc.on('reader', reader => {
            console.log(`🔌 Device attached: ${reader.reader.name}`);

            reader.on('card', async card => {
                console.log(`💳 Card detected. UID: ${card.uid}`);

                const keyType = 0x60;
                const key = 'FFFFFFFFFFFF';
                const startBlock = 4; // first writable block after manufacturer data

                try {
                    const jsonString = JSON.stringify(formData);
                    const buffer = Buffer.from(jsonString, 'utf8');

                    const chunks = [];
                    for (let i = 0; i < buffer.length; i += 16) {
                        chunks.push(buffer.slice(i, i + 16));
                    }

                    for (let i = 0, blockNum = startBlock; i < chunks.length; blockNum++) {
                        if ((blockNum + 1) % 4 === 0) {
                            console.log(`⚠️ Skipping sector trailer at block ${blockNum}`);
                            continue;
                        }

                        await reader.authenticate(blockNum, keyType, Buffer.from(key, 'hex'));
                        const paddedChunk = Buffer.alloc(16);
                        chunks[i].copy(paddedChunk);

                        await reader.write(blockNum, paddedChunk, 16);
                        console.log(`✅ Written to block ${blockNum}: "${paddedChunk.toString('utf8')}"`);
                        i++;
                    }

                    reader.close();
                    resolve(`Card written successfully: ${chunks.length} blocks used`);
                } catch (err) {
                    reject(`❌ Error writing card: ${err}`);
                }
            });

            reader.on('error', err => reject(`❌ Reader error: ${err}`));
        });

        nfc.on('error', err => reject(`❌ NFC error: ${err}`));
    });
};
