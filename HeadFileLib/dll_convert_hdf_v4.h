#include "extcode.h"
#ifdef __cplusplus
extern "C" {
#endif
typedef uint16_t  Enum;
#define Enum_utf8Code 0
#define Enum_gbk_code 1

/*!
 * DLL_hdf_convert_v4
 */
void __cdecl DLL_hdf_convert_v4(char source_input[], Enum *encode_enum, 
	int64_t data_mini_batch_size, char path_out[], char ErrorStatus[], 
	int32_t len_pathout, int32_t len_err);

MgErr __cdecl LVDLLStatus(char *errStr, int errStrLen, void *module);

void __cdecl SetExecuteVIsInPrivateExecutionSystem(Bool32 value);

#ifdef __cplusplus
} // extern "C"
#endif

