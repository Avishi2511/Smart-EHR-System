import { NFC } from 'nfc-pcsc';

export const readFromCard = async () => {
    return new Promise((resolve, reject) => {
        const nfc = new NFC();

        nfc.on('reader', reader => {
            console.log(`🔌 Device attached: ${reader.reader.name}`);

            reader.on('card', async card => {
                console.log(`💳 Card detected. UID: ${card.uid}`);

                const keyType = 0x60;
                const key = 'FFFFFFFFFFFF';
                const startBlock = 4;
                const endBlock = 63; // Mifare Classic 1K max

                try {
                    let fullBuffer = Buffer.alloc(0);

                    for (let blockNum = startBlock; blockNum <= endBlock; blockNum++) {
                        if ((blockNum + 1) % 4 === 0) {
                            console.log(`⚠️ Skipping sector trailer at block ${blockNum}`);
                            continue;
                        }

                        await reader.authenticate(blockNum, keyType, Buffer.from(key, 'hex'));
                        const data = await reader.read(blockNum, 16, 16);
                        fullBuffer = Buffer.concat([fullBuffer, data]);
                    }

                    const jsonString = fullBuffer.toString('utf8').replace(/\0/g, '').trim();
                    console.log(`📖 Full Data: ${jsonString}`);

                    reader.close();
                    resolve(JSON.parse(jsonString));
                } catch (err) {
                    reject(`❌ Error reading card: ${err}`);
                }
            });

            reader.on('error', err => reject(`❌ Reader error: ${err}`));
        });

        nfc.on('error', err => reject(`❌ NFC error: ${err}`));
    });
};
