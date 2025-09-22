"""
Experimento de Rendimiento - Saga Pattern
Valida si el patrón saga puede manejar la carga esperada con latencias aceptables
"""
import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime, timezone
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import uuid

# Configuración del experimento
BFF_BASE_URL = "http://localhost:8000"
CONCURRENT_REQUESTS = 10
TOTAL_REQUESTS = 100
TIMEOUT_SECONDS = 30

class PerformanceExperiment:
    def __init__(self):
        self.results = []
        self.errors = []
        
    async def create_saga_request(self, session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
        """Crear una request de saga individual"""
        start_time = time.time()
        
        payload = {
            "affiliate_name": f"Test User {request_id}",
            "affiliate_email": f"test.user.{request_id}@example.com",
            "commission_rate": 0.15,
            "content_type": "BLOG",
            "content_title": f"Content Title {request_id}",
            "content_description": f"Test content description for request {request_id}",
            "collaboration_type": "CONTENT_CREATION"
        }
        
        try:
            async with session.post(
                f"{BFF_BASE_URL}/api/v1/sagas/complete-affiliate-registration",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
            ) as response:
                end_time = time.time()
                latency = (end_time - start_time) * 1000  # ms
                
                response_data = await response.json()
                
                return {
                    "request_id": request_id,
                    "status_code": response.status,
                    "latency_ms": latency,
                    "saga_id": response_data.get("saga_id"),
                    "success": response.status == 200,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            return {
                "request_id": request_id,
                "status_code": 0,
                "latency_ms": latency,
                "saga_id": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def check_saga_status(self, session: aiohttp.ClientSession, saga_id: str) -> Dict[str, Any]:
        """Verificar estado de una saga"""
        try:
            async with session.get(
                f"{BFF_BASE_URL}/api/v1/sagas/{saga_id}/status",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "saga_id": saga_id,
                        "status": data.get("status"),
                        "steps_count": len(data.get("steps", [])),
                        "success": True
                    }
                else:
                    return {"saga_id": saga_id, "success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"saga_id": saga_id, "success": False, "error": str(e)}
    
    async def run_batch(self, batch_size: int, batch_number: int) -> List[Dict[str, Any]]:
        """Ejecutar un lote de requests concurrentes"""
        print(f"Ejecutando lote {batch_number} con {batch_size} requests...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            start_request_id = batch_number * batch_size
            
            for i in range(batch_size):
                request_id = start_request_id + i
                task = self.create_saga_request(session, request_id)
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filtrar resultados válidos
            valid_results = []
            for result in batch_results:
                if isinstance(result, dict):
                    valid_results.append(result)
                else:
                    print(f"Error en lote {batch_number}: {result}")
            
            return valid_results
    
    async def run_performance_test(self) -> Dict[str, Any]:
        """Ejecutar el experimento completo de rendimiento"""
        print("Iniciando Experimento de Rendimiento de Saga...")
        print(f"   - Requests totales: {TOTAL_REQUESTS}")
        print(f"   - Concurrencia: {CONCURRENT_REQUESTS}")
        print(f"   - URL objetivo: {BFF_BASE_URL}")
        
        start_time = time.time()
        
        # Ejecutar requests en lotes
        batches = TOTAL_REQUESTS // CONCURRENT_REQUESTS
        remaining = TOTAL_REQUESTS % CONCURRENT_REQUESTS
        
        all_results = []
        
        for batch in range(batches):
            batch_results = await self.run_batch(CONCURRENT_REQUESTS, batch)
            all_results.extend(batch_results)
            
            # Pequeña pausa entre lotes
            await asyncio.sleep(0.1)
        
        # Lote final con requests restantes
        if remaining > 0:
            batch_results = await self.run_batch(remaining, batches)
            all_results.extend(batch_results)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        return self.analyze_results(all_results, total_duration)
    
    def analyze_results(self, results: List[Dict[str, Any]], total_duration: float) -> Dict[str, Any]:
        """Analizar resultados del experimento"""
        successful_requests = [r for r in results if r.get("success", False)]
        failed_requests = [r for r in results if not r.get("success", False)]
        
        if not successful_requests:
            return {
                "status": "FAILED",
                "error": "No successful requests",
                "total_requests": len(results),
                "failed_requests": len(failed_requests)
            }
        
        latencies = [r["latency_ms"] for r in successful_requests]
        
        analysis = {
            "experiment_type": "performance",
            "status": "COMPLETED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "configuration": {
                "total_requests": TOTAL_REQUESTS,
                "concurrent_requests": CONCURRENT_REQUESTS,
                "timeout_seconds": TIMEOUT_SECONDS
            },
            "results": {
                "total_duration_seconds": round(total_duration, 2),
                "total_requests": len(results),
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "success_rate": round(len(successful_requests) / len(results) * 100, 2),
                "throughput_requests_per_second": round(len(successful_requests) / total_duration, 2),
                "latency_stats": {
                    "min_ms": round(min(latencies), 2),
                    "max_ms": round(max(latencies), 2),
                    "mean_ms": round(statistics.mean(latencies), 2),
                    "median_ms": round(statistics.median(latencies), 2),
                    "p95_ms": round(statistics.quantiles(latencies, n=20)[18], 2),  # 95th percentile
                    "p99_ms": round(statistics.quantiles(latencies, n=100)[98], 2)  # 99th percentile
                }
            },
            "hypothesis_validation": {
                "expected_throughput": 100,  # requests/min
                "expected_p95_latency": 2000,  # ms
                "actual_throughput": round(len(successful_requests) / total_duration * 60, 2),
                "actual_p95_latency": round(statistics.quantiles(latencies, n=20)[18], 2),
                "throughput_met": (len(successful_requests) / total_duration * 60) >= 100,
                "latency_met": statistics.quantiles(latencies, n=20)[18] <= 2000
            },
            "errors": [{"request_id": r["request_id"], "error": r.get("error", "Unknown")} 
                      for r in failed_requests[:10]]  # Primeros 10 errores
        }
        
        # Verificar si se cumple la hipótesis
        hypothesis_met = (analysis["hypothesis_validation"]["throughput_met"] and 
                         analysis["hypothesis_validation"]["latency_met"])
        
        analysis["conclusion"] = {
            "hypothesis_met": hypothesis_met,
            "summary": self.generate_conclusion_summary(analysis)
        }
        
        return analysis
    
    def generate_conclusion_summary(self, analysis: Dict[str, Any]) -> str:
        """Generar resumen de conclusiones"""
        results = analysis["results"]
        hypothesis = analysis["hypothesis_validation"]
        
        if analysis["conclusion"]["hypothesis_met"]:
            return (f"HIPÓTESIS CUMPLIDA: El sistema procesó {results['successful_requests']} "
                   f"sagas con {results['throughput_requests_per_second']:.1f} req/s "
                   f"y P95 latency de {results['latency_stats']['p95_ms']:.1f}ms")
        else:
            issues = []
            if not hypothesis["throughput_met"]:
                issues.append(f"throughput insuficiente ({hypothesis['actual_throughput']:.1f} < 100 req/min)")
            if not hypothesis["latency_met"]:
                issues.append(f"latencia alta ({hypothesis['actual_p95_latency']:.1f}ms > 2000ms)")
            
            return f"HIPÓTESIS NO CUMPLIDA: {', '.join(issues)}"

async def main():
    experiment = PerformanceExperiment()
    
    print("🔬 EXPERIMENTO DE RENDIMIENTO - PATRÓN SAGA")
    print("=" * 60)
    
    try:
        results = await experiment.run_performance_test()
        
        # Guardar resultados
        with open("performance_experiment_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Mostrar resumen
        print("\nRESULTADOS DEL EXPERIMENTO")
        print("=" * 40)
        print(f"Status: {results['status']}")
        print(f"Requests exitosos: {results['results']['successful_requests']}/{results['results']['total_requests']}")
        print(f"Tasa de éxito: {results['results']['success_rate']}%")
        print(f"Throughput: {results['results']['throughput_requests_per_second']} req/s")
        print(f"Latencia media: {results['results']['latency_stats']['mean_ms']}ms")
        print(f"Latencia P95: {results['results']['latency_stats']['p95_ms']}ms")
        print()
        print("VALIDACIÓN DE HIPÓTESIS")
        print("=" * 30)
        print(results['conclusion']['summary'])
        
        print(f"\nResultados guardados en: performance_experiment_results.json")
        
    except Exception as e:
        print(f"Error en experimento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())